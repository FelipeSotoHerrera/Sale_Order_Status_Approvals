# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([('draft', 'Quotation'),
                              ('sent', 'Quotation Sent'),
                              ('draft_ok', 'Validated Budget'),
                              ('commercial_state', 'Commercially approved'),
                              ('financial_state', 'Financially Approved'),
                              ('sale', 'Sales Order'),
                              ('invoiced', 'Invoiced'),
                              ('done', 'Locked'),
                              ('cancel', 'Cancelled'),], string='Status', readonly=True, copy=False, index=True,
                             track_visibility='onchange', default='draft')

    @api.multi
    def _make_url(self, model, id):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url', default='http://localhost:8069')
        if base_url:
            base_url += '/web/login?db=%s&login=%s&key=%s#id=%s&model=%s' % (self._cr.dbname, '', '', id, model)
        return base_url

    @api.multi
    def action_confirm_draft(self):
        for order in self:
            if order.state not in ['draft']:
                continue
            else:
                if order.company_id.commercial_approval == 'disabled':
                    if order.company_id.financial_approval == 'disabled':
                        if order.company_id.creation_sale_orders_permits == 'disabled':
                            if order.company_id.generation_sales_invoices == 'disabled':
                                if order.company_id.validation_sales_invoices == 'disabled':
                                    raise UserError(_('at least one state must be enabled'))
                                elif order.company_id.validation_sales_invoices == 'enabled':
                                    return super(SaleOrder, self).action_confirm()
                            elif order.company_id.generation_sales_invoices == 'enabled':
                                return super(SaleOrder, self).action_confirm()
                        elif order.company_id.creation_sale_orders_permits  == 'enabled':
                            order.write({'state': 'financial_state'})
                    elif order.company_id.financial_approval == 'enabled':
                        order.write({'state': 'commercial_state'})
                elif order.company_id.commercial_approval == 'enabled' and order.amount_total > self.env.user.company_id.currency_id.compute(order.company_id.commercial_approval_amount, order.currency_id):
                    authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                    authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                    so_url = order._make_url('sale.order', order.id)

                    names_commercial = order.user_id.names_commercial_notifications
                    names_administrators = order.user_id.names_administrators_notifications
                    verify_user = authorized_notifications_users
                    active_user = False
                    receiver_commercial = ''
                    receiver_administrator = ''
                    count_names_commercial = 0
                    count_names_administrators = 0
                    language = order.user_id.lang.split('_')
                    general_language = language[0]

                    for user_salesman in verify_user:
                        if user_salesman.id == order.user_id.id:
                            active_user = True
                            break
                        else:
                            active_user = False

                    if active_user == True:
                        if general_language == 'es':
                            if order.user_id.mail_commercial_notifications != '':
                                for mail in order.user_id.mail_commercial_notifications.split(','):
                                    if mail != '':
                                        limit = count_names_commercial
                                        count_one_name = 0
                                        for name_comercial in names_commercial.split(','):
                                            if count_one_name == limit:
                                                receiver_commercial = name_comercial
                                                break
                                            else:
                                                count_one_name = count_one_name + 1

                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                       El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                 <div style="margin-top:40px;">
                                                                                                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                 font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                 <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' Validado por Vendedor',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': mail,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                                        count_names_commercial = count_names_commercial + 1

                            if order.company_id.administrators_notifications == 'enabled':
                                if order.user_id.mail_administrators_notifications != '':
                                    for mail in order.user_id.mail_administrators_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_administrators
                                            count_one_name = 0
                                            for name_administrator in names_administrators.split(','):
                                                if count_one_name == limit:
                                                    receiver_administrator = name_administrator
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                         % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                          El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Presupuesto N°' + str(order.name) + ' Validado por Vendedor',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_administrators = count_names_administrators + 1

                            if order.company_id.sellers_notifications == 'enabled':
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                      Has validado el presupuesto N°<span style='font-weight: bold;'>%s</span> y espera aprobación comercial</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Puedes verlo haciendo click</span> \
                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                     <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' Validado',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                        else:
                            if order.user_id.mail_commercial_notifications != '':
                                for mail in order.user_id.mail_commercial_notifications.split(','):
                                    if mail != '':
                                        limit = count_names_commercial
                                        count_one_name = 0
                                        for name_comercial in names_commercial.split(','):
                                            if count_one_name == limit:
                                                receiver_commercial = name_comercial
                                                break
                                            else:
                                                count_one_name = count_one_name + 1

                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                     % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                 The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                 <div style="margin-top:40px;">
                                                                                                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                 font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                 <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': mail,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                                        count_names_commercial = count_names_commercial + 1

                            if order.company_id.administrators_notifications == 'enabled':
                                if order.user_id.mail_administrators_notifications != '':
                                    for mail in order.user_id.mail_administrators_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_administrators
                                            count_one_name = 0
                                            for name_administrator in names_administrators.split(','):
                                                if count_one_name == limit:
                                                    receiver_administrator = name_administrator
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                     The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_administrators = count_names_administrators + 1

                            if order.company_id.sellers_notifications == 'enabled':
                                if authorized_notifications_users:
                                    for au_user in authorized_notifications_users:
                                        if au_user.id == order.user_id.id:
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                         You have validated the Budget <span style='font-weight: bold;'>%s</span> and I await commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>You can see it by clicking</span> \
                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                         <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': au_user.partner_id.email,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()

                        order.write({'state': 'draft_ok'})
                    else:
                        if general_language == 'es':
                            raise UserError(_('El usuario: ' + order.user_id.name + ', no tiene habilitado las notificaciones para vendedores.'))
                        else:
                            raise UserError(_('The user: ' + order.user_id.name + ', you don t have vendor notifications enabled.'))
                elif order.company_id.commercial_approval == 'enabled' and order.amount_total == self.env.user.company_id.currency_id.compute(order.company_id.commercial_approval_amount, order.currency_id):
                    authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                    authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                    so_url = order._make_url('sale.order', order.id)

                    names_commercial = order.user_id.names_commercial_notifications
                    names_administrators = order.user_id.names_administrators_notifications
                    verify_user = authorized_notifications_users
                    active_user = False
                    receiver_commercial = ''
                    receiver_administrator = ''
                    count_names_commercial = 0
                    count_names_administrators = 0
                    language = order.user_id.lang.split('_')
                    general_language = language[0]

                    for user_salesman in verify_user:
                        if user_salesman.id == order.user_id.id:
                            active_user = True
                            break
                        else:
                            active_user = False

                    if active_user == True:
                        if general_language == 'es':
                            if order.user_id.mail_commercial_notifications != '':
                                for mail in order.user_id.mail_commercial_notifications.split(','):
                                    if mail != '':
                                        limit = count_names_commercial
                                        count_one_name = 0
                                        for name_comercial in names_commercial.split(','):
                                            if count_one_name == limit:
                                                receiver_commercial = name_comercial
                                                break
                                            else:
                                                count_one_name = count_one_name + 1

                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                           El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                                     <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' Validado por Vendedor',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': mail,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                                        count_names_commercial = count_names_commercial + 1

                            if order.company_id.administrators_notifications == 'enabled':
                                if order.user_id.mail_administrators_notifications != '':
                                    for mail in order.user_id.mail_administrators_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_administrators
                                            count_one_name = 0
                                            for name_administrator in names_administrators.split(','):
                                                if count_one_name == limit:
                                                    receiver_administrator = name_administrator
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                         % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                              El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                                         <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Presupuesto N°' + str(
                                                    order.name) + ' Validado por Vendedor',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_administrators = count_names_administrators + 1

                            if order.company_id.sellers_notifications == 'enabled':
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                          Has validado el presupuesto N°<span style='font-weight: bold;'>%s</span> y espera aprobación comercial</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Puedes verlo haciendo click</span> \
                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                         <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' Validado',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                        else:
                            if order.user_id.mail_commercial_notifications != '':
                                for mail in order.user_id.mail_commercial_notifications.split(','):
                                    if mail != '':
                                        limit = count_names_commercial
                                        count_one_name = 0
                                        for name_comercial in names_commercial.split(','):
                                            if count_one_name == limit:
                                                receiver_commercial = name_comercial
                                                break
                                            else:
                                                count_one_name = count_one_name + 1

                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                     % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                     The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                     <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': mail,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                                        count_names_commercial = count_names_commercial + 1

                            if order.company_id.administrators_notifications == 'enabled':
                                if order.user_id.mail_administrators_notifications != '':
                                    for mail in order.user_id.mail_administrators_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_administrators
                                            count_one_name = 0
                                            for name_administrator in names_administrators.split(','):
                                                if count_one_name == limit:
                                                    receiver_administrator = name_administrator
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                         The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                         <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_administrators = count_names_administrators + 1

                            if order.company_id.sellers_notifications == 'enabled':
                                if authorized_notifications_users:
                                    for au_user in authorized_notifications_users:
                                        if au_user.id == order.user_id.id:
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                             You have validated the Budget <span style='font-weight: bold;'>%s</span> and I await commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>You can see it by clicking</span> \
                                                                                                                                                                                                             <div style="margin-top:40px;">
                                                                                                                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                             font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                             <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': au_user.partner_id.email,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()

                        order.write({'state': 'draft_ok'})
                    else:
                        if general_language == 'es':
                            raise UserError(_('El usuario: ' + order.user_id.name + ', no tiene habilitado las notificaciones para vendedores.'))
                        else:
                            raise UserError(_('The user: ' + order.user_id.name + ', you don t have vendor notifications enabled.'))
                elif order.company_id.commercial_approval == 'enabled' and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.commercial_approval_amount, order.currency_id):
                    authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                    authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                    so_url = order._make_url('sale.order', order.id)

                    names_commercial = order.user_id.names_commercial_notifications
                    names_administrators = order.user_id.names_administrators_notifications
                    verify_user = authorized_notifications_users
                    active_user = False
                    receiver_commercial = ''
                    receiver_administrator = ''
                    count_names_commercial = 0
                    count_names_administrators = 0
                    language = order.user_id.lang.split('_')
                    general_language = language[0]

                    for user_salesman in verify_user:
                        if user_salesman.id == order.user_id.id:
                            active_user = True
                            break
                        else:
                            active_user = False

                    # if order.user_id.employee_ids.job_id.display_name == 'Vendedor Delivery':
                    if active_user == True:
                        if general_language == 'es':
                            if order.user_id.employee_ids.job_id.display_name == 'Vendedor Delivery':
                                if order.user_id.mail_commercial_notifications != '':
                                    for mail in order.user_id.mail_commercial_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_commercial
                                            count_one_name = 0
                                            for name_comercial in names_commercial.split(','):
                                                if count_one_name == limit:
                                                    receiver_commercial = name_comercial
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1

                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                         % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                           El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Presupuesto N°' + str(
                                                    order.name) + ' Validado por Vendedor',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_commercial = count_names_commercial + 1

                                if order.company_id.administrators_notifications == 'enabled':
                                    if order.user_id.mail_administrators_notifications != '':
                                        for mail in order.user_id.mail_administrators_notifications.split(','):
                                            if mail != '':
                                                limit = count_names_administrators
                                                count_one_name = 0
                                                for name_administrator in names_administrators.split(','):
                                                    if count_one_name == limit:
                                                        receiver_administrator = name_administrator
                                                        break
                                                    else:
                                                        count_one_name = count_one_name + 1
                                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                             % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                              El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                                 order.name) + ''' <br/>''' \
                                                             + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                         <br/><br/>'''
                                                email_id = self.env['mail.mail'].create(
                                                    {'subject': 'Presupuesto N°' + str(
                                                        order.name) + ' Validado por Vendedor',
                                                     'email_from': self.env.user.partner_id.email,
                                                     'email_to': mail,
                                                     'message_type': 'email',
                                                     'body_html': email_body,
                                                     })
                                                email_id.send()
                                                count_names_administrators = count_names_administrators + 1

                                if order.company_id.sellers_notifications == 'enabled':
                                    for au_user in authorized_notifications_users:
                                        if au_user.id == order.user_id.id:
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                          Has validado el presupuesto N°<span style='font-weight: bold;'>%s</span> y espera aprobación comercial</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Puedes verlo haciendo click</span> \
                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                         <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Presupuesto N°' + str(order.name) + ' Validado',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': au_user.partner_id.email,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()

                                order.write({'state': 'draft_ok'})
                            else:
                                raise UserError(_('El monto total del pedido de venta es inferior al permitido, mínimo: ' + str(round(order.company_id.commercial_approval_amount))))
                        else:
                            if order.user_id.employee_ids.job_id.display_name == 'Delivery Salesman':
                                if order.user_id.mail_commercial_notifications != '':
                                    for mail in order.user_id.mail_commercial_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_commercial
                                            count_one_name = 0
                                            for name_comercial in names_commercial.split(','):
                                                if count_one_name == limit:
                                                    receiver_commercial = name_comercial
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1

                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                     The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_commercial = count_names_commercial + 1

                                if order.company_id.administrators_notifications == 'enabled':
                                    if order.user_id.mail_administrators_notifications != '':
                                        for mail in order.user_id.mail_administrators_notifications.split(','):
                                            if mail != '':
                                                limit = count_names_administrators
                                                count_one_name = 0
                                                for name_administrator in names_administrators.split(','):
                                                    if count_one_name == limit:
                                                        receiver_administrator = name_administrator
                                                        break
                                                    else:
                                                        count_one_name = count_one_name + 1
                                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                             % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                         The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                                 order.name) + ''' <br/>''' \
                                                             + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                         <br/><br/>'''
                                                email_id = self.env['mail.mail'].create(
                                                    {'subject': 'Quote N°' + str(
                                                        order.name) + ' Validated by Seller',
                                                     'email_from': self.env.user.partner_id.email,
                                                     'email_to': mail,
                                                     'message_type': 'email',
                                                     'body_html': email_body,
                                                     })
                                                email_id.send()
                                                count_names_administrators = count_names_administrators + 1

                                if order.company_id.sellers_notifications == 'enabled':
                                    if authorized_notifications_users:
                                        for au_user in authorized_notifications_users:
                                            if au_user.id == order.user_id.id:
                                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                             You have validated the Budget <span style='font-weight: bold;'>%s</span> and I await commercial approval</span>''' % (
                                                                 order.name) + ''' <br/>''' \
                                                             + '''<span style='font-style: 14px;'>You can see it by clicking</span> \
                                                                                                                                                                                             <div style="margin-top:40px;">
                                                                                                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                             font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                             <br/><br/>'''
                                                email_id = self.env['mail.mail'].create(
                                                    {'subject': 'Quote N°' + str(order.name) + ' Validated',
                                                     'email_from': self.env.user.partner_id.email,
                                                     'email_to': au_user.partner_id.email,
                                                     'message_type': 'email',
                                                     'body_html': email_body,
                                                     })
                                                email_id.send()

                                order.write({'state': 'draft_ok'})
                            else:
                                raise UserError(_('The total amount of the sales order is less than allowed, minimum: ' + str(round(order.company_id.commercial_approval_amount))))
                    else:
                        if general_language == 'es':
                            raise UserError(_('El usuario: ' + order.user_id.name + ', no tiene habilitado las notificaciones para vendedores.'))
                        else:
                            raise UserError(_('The user: ' + order.user_id.name + ', you don t have vendor notifications enabled.'))

    @api.multi
    def action_confirm_sent(self):
        for order in self:
            if order.state not in ['sent']:
                continue
            else:
                if order.company_id.commercial_approval == 'disabled':
                    if order.company_id.financial_approval == 'disabled':
                        if order.company_id.creation_sale_orders_permits == 'disabled':
                            if order.company_id.generation_sales_invoices == 'disabled':
                                if order.company_id.validation_sales_invoices == 'disabled':
                                    raise UserError(_('at least one state must be enabled'))
                                elif order.company_id.validation_sales_invoices == 'enabled':
                                    return super(SaleOrder, self).action_confirm()
                            elif order.company_id.generation_sales_invoices == 'enabled':
                                return super(SaleOrder, self).action_confirm()
                        elif order.company_id.creation_sale_orders_permits == 'enabled':
                            order.write({'state': 'financial_state'})
                    elif order.company_id.financial_approval == 'enabled':
                        order.write({'state': 'commercial_state'})
                elif order.company_id.commercial_approval == 'enabled' and order.amount_total > self.env.user.company_id.currency_id.compute(order.company_id.commercial_approval_amount, order.currency_id):
                    authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                    authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                    so_url = order._make_url('sale.order', order.id)

                    names_commercial = order.user_id.names_commercial_notifications
                    names_administrators = order.user_id.names_administrators_notifications
                    verify_user = authorized_notifications_users
                    active_user = False
                    receiver_commercial = ''
                    receiver_administrator = ''
                    count_names_commercial = 0
                    count_names_administrators = 0
                    language = order.user_id.lang.split('_')
                    general_language = language[0]

                    for user_salesman in verify_user:
                        if user_salesman.id == order.user_id.id:
                            active_user = True
                            break
                        else:
                            active_user = False

                    if active_user == True:
                        if general_language == 'es':
                            if order.user_id.mail_commercial_notifications != '':
                                for mail in order.user_id.mail_commercial_notifications.split(','):
                                    if mail != '':
                                        limit = count_names_commercial
                                        count_one_name = 0
                                        for name_comercial in names_commercial.split(','):
                                            if count_one_name == limit:
                                                receiver_commercial = name_comercial
                                                break
                                            else:
                                                count_one_name = count_one_name + 1

                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                       El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                 <div style="margin-top:40px;">
                                                                                                                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                 font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                                 <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' Validado por Vendedor',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': mail,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                                        count_names_commercial = count_names_commercial + 1

                            if order.company_id.administrators_notifications == 'enabled':
                                if order.user_id.mail_administrators_notifications != '':
                                    for mail in order.user_id.mail_administrators_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_administrators
                                            count_one_name = 0
                                            for name_administrator in names_administrators.split(','):
                                                if count_one_name == limit:
                                                    receiver_administrator = name_administrator
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                         % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                          El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                                     <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Presupuesto N°' + str(
                                                    order.name) + ' Validado por Vendedor',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_administrators = count_names_administrators + 1

                            if order.company_id.sellers_notifications == 'enabled':
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                      Has validado el presupuesto N°<span style='font-weight: bold;'>%s</span> y espera aprobación comercial</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Puedes verlo haciendo click</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' Validado',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                        else:
                            if order.user_id.mail_commercial_notifications != '':
                                for mail in order.user_id.mail_commercial_notifications.split(','):
                                    if mail != '':
                                        limit = count_names_commercial
                                        count_one_name = 0
                                        for name_comercial in names_commercial.split(','):
                                            if count_one_name == limit:
                                                receiver_commercial = name_comercial
                                                break
                                            else:
                                                count_one_name = count_one_name + 1

                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                     % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                 The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                 <div style="margin-top:40px;">
                                                                                                                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                 font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                 <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': mail,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                                        count_names_commercial = count_names_commercial + 1

                            if order.company_id.administrators_notifications == 'enabled':
                                if order.user_id.mail_administrators_notifications != '':
                                    for mail in order.user_id.mail_administrators_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_administrators
                                            count_one_name = 0
                                            for name_administrator in names_administrators.split(','):
                                                if count_one_name == limit:
                                                    receiver_administrator = name_administrator
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                     The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                     <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_administrators = count_names_administrators + 1

                            if order.company_id.sellers_notifications == 'enabled':
                                if authorized_notifications_users:
                                    for au_user in authorized_notifications_users:
                                        if au_user.id == order.user_id.id:
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                         You have validated the Budget <span style='font-weight: bold;'>%s</span> and I await commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>You can see it by clicking</span> \
                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                         <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': au_user.partner_id.email,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()

                        order.write({'state': 'draft_ok'})
                    else:
                        if general_language == 'es':
                            raise UserError(_('El usuario: ' + order.user_id.name + ', no tiene habilitado las notificaciones para vendedores.'))
                        else:
                            raise UserError(_('The user: ' + order.user_id.name + ', you don t have vendor notifications enabled.'))
                elif order.company_id.commercial_approval == 'enabled' and order.amount_total == self.env.user.company_id.currency_id.compute(order.company_id.commercial_approval_amount, order.currency_id):
                    authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                    authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                    so_url = order._make_url('sale.order', order.id)

                    names_commercial = order.user_id.names_commercial_notifications
                    names_administrators = order.user_id.names_administrators_notifications
                    verify_user = authorized_notifications_users
                    active_user = False
                    receiver_commercial = ''
                    receiver_administrator = ''
                    count_names_commercial = 0
                    count_names_administrators = 0
                    language = order.user_id.lang.split('_')
                    general_language = language[0]

                    for user_salesman in verify_user:
                        if user_salesman.id == order.user_id.id:
                            active_user = True
                            break
                        else:
                            active_user = False

                    if active_user == True:
                        if general_language == 'es':
                            if order.user_id.mail_commercial_notifications != '':
                                for mail in order.user_id.mail_commercial_notifications.split(','):
                                    if mail != '':
                                        limit = count_names_commercial
                                        count_one_name = 0
                                        for name_comercial in names_commercial.split(','):
                                            if count_one_name == limit:
                                                receiver_commercial = name_comercial
                                                break
                                            else:
                                                count_one_name = count_one_name + 1

                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                           El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                                                     <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' Validado por Vendedor',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': mail,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                                        count_names_commercial = count_names_commercial + 1

                            if order.company_id.administrators_notifications == 'enabled':
                                if order.user_id.mail_administrators_notifications != '':
                                    for mail in order.user_id.mail_administrators_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_administrators
                                            count_one_name = 0
                                            for name_administrator in names_administrators.split(','):
                                                if count_one_name == limit:
                                                    receiver_administrator = name_administrator
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                         % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                              El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                                                         <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Presupuesto N°' + str(
                                                    order.name) + ' Validado por Vendedor',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_administrators = count_names_administrators + 1

                            if order.company_id.sellers_notifications == 'enabled':
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                          Has validado el presupuesto N°<span style='font-weight: bold;'>%s</span> y espera aprobación comercial</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Puedes verlo haciendo click</span> \
                                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                                         <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' Validado',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                        else:
                            if order.user_id.mail_commercial_notifications != '':
                                for mail in order.user_id.mail_commercial_notifications.split(','):
                                    if mail != '':
                                        limit = count_names_commercial
                                        count_one_name = 0
                                        for name_comercial in names_commercial.split(','):
                                            if count_one_name == limit:
                                                receiver_commercial = name_comercial
                                                break
                                            else:
                                                count_one_name = count_one_name + 1

                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                     % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                                     The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                                     <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': mail,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()
                                        count_names_commercial = count_names_commercial + 1

                            if order.company_id.administrators_notifications == 'enabled':
                                if order.user_id.mail_administrators_notifications != '':
                                    for mail in order.user_id.mail_administrators_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_administrators
                                            count_one_name = 0
                                            for name_administrator in names_administrators.split(','):
                                                if count_one_name == limit:
                                                    receiver_administrator = name_administrator
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                                         The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                                         <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_administrators = count_names_administrators + 1

                            if order.company_id.sellers_notifications == 'enabled':
                                if authorized_notifications_users:
                                    for au_user in authorized_notifications_users:
                                        if au_user.id == order.user_id.id:
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                             You have validated the Budget <span style='font-weight: bold;'>%s</span> and I await commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>You can see it by clicking</span> \
                                                                                                                                                                                                                             <div style="margin-top:40px;">
                                                                                                                                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                             font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                             <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': au_user.partner_id.email,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()

                        order.write({'state': 'draft_ok'})
                    else:
                        if general_language == 'es':
                            raise UserError(_('El usuario: ' + order.user_id.name + ', no tiene habilitado las notificaciones para vendedores.'))
                        else:
                            raise UserError(_('The user: ' + order.user_id.name + ', you don t have vendor notifications enabled.'))
                elif order.company_id.commercial_approval == 'enabled' and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.commercial_approval_amount, order.currency_id):
                    authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                    authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                    so_url = order._make_url('sale.order', order.id)

                    names_commercial = order.user_id.names_commercial_notifications
                    names_administrators = order.user_id.names_administrators_notifications
                    verify_user = authorized_notifications_users
                    active_user = False
                    receiver_commercial = ''
                    receiver_administrator = ''
                    count_names_commercial = 0
                    count_names_administrators = 0
                    language = order.user_id.lang.split('_')
                    general_language = language[0]

                    for user_salesman in verify_user:
                        if user_salesman.id == order.user_id.id:
                            active_user = True
                            break
                        else:
                            active_user = False

                    # if order.user_id.employee_ids.job_id.display_name == 'Vendedor Delivery':
                    if active_user == True:
                        if general_language == 'es':
                            if order.user_id.employee_ids.job_id.display_name == 'Vendedor Delivery':
                                if order.user_id.mail_commercial_notifications != '':
                                    for mail in order.user_id.mail_commercial_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_commercial
                                            count_one_name = 0
                                            for name_comercial in names_commercial.split(','):
                                                if count_one_name == limit:
                                                    receiver_commercial = name_comercial
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1

                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                         % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                           El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                                     <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Presupuesto N°' + str(
                                                    order.name) + ' Validado por Vendedor',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_commercial = count_names_commercial + 1

                                if order.company_id.administrators_notifications == 'enabled':
                                    if order.user_id.mail_administrators_notifications != '':
                                        for mail in order.user_id.mail_administrators_notifications.split(','):
                                            if mail != '':
                                                limit = count_names_administrators
                                                count_one_name = 0
                                                for name_administrator in names_administrators.split(','):
                                                    if count_one_name == limit:
                                                        receiver_administrator = name_administrator
                                                        break
                                                    else:
                                                        count_one_name = count_one_name + 1
                                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                             % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                              El Presupuesto N°<span style='font-weight: bold;'>%s</span> ha sido validado y espera aprobación comercial.</span>''' % (
                                                                 order.name) + ''' <br/>''' \
                                                             + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                                         <br/><br/>'''
                                                email_id = self.env['mail.mail'].create(
                                                    {'subject': 'Presupuesto N°' + str(
                                                        order.name) + ' Validado por Vendedor',
                                                     'email_from': self.env.user.partner_id.email,
                                                     'email_to': mail,
                                                     'message_type': 'email',
                                                     'body_html': email_body,
                                                     })
                                                email_id.send()
                                                count_names_administrators = count_names_administrators + 1

                                if order.company_id.sellers_notifications == 'enabled':
                                    for au_user in authorized_notifications_users:
                                        if au_user.id == order.user_id.id:
                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                          Has validado el presupuesto N°<span style='font-weight: bold;'>%s</span> y espera aprobación comercial</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Puedes verlo haciendo click</span> \
                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                         <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Presupuesto N°' + str(order.name) + ' Validado',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': au_user.partner_id.email,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()

                                order.write({'state': 'draft_ok'})
                            else:
                                raise UserError(_('El monto total del pedido de venta es inferior al permitido, mínimo: ' + str(round(order.company_id.commercial_approval_amount))))
                        else:
                            if order.user_id.employee_ids.job_id.display_name == 'Delivery Salesman':
                                if order.user_id.mail_commercial_notifications != '':
                                    for mail in order.user_id.mail_commercial_notifications.split(','):
                                        if mail != '':
                                            limit = count_names_commercial
                                            count_one_name = 0
                                            for name_comercial in names_commercial.split(','):
                                                if count_one_name == limit:
                                                    receiver_commercial = name_comercial
                                                    break
                                                else:
                                                    count_one_name = count_one_name + 1

                                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                         % (receiver_commercial) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                     The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                             order.name) + ''' <br/>''' \
                                                         + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                     <br/><br/>'''
                                            email_id = self.env['mail.mail'].create(
                                                {'subject': 'Quote N°' + str(order.name) + ' Validated by Seller',
                                                 'email_from': self.env.user.partner_id.email,
                                                 'email_to': mail,
                                                 'message_type': 'email',
                                                 'body_html': email_body,
                                                 })
                                            email_id.send()
                                            count_names_commercial = count_names_commercial + 1

                                if order.company_id.administrators_notifications == 'enabled':
                                    if order.user_id.mail_administrators_notifications != '':
                                        for mail in order.user_id.mail_administrators_notifications.split(','):
                                            if mail != '':
                                                limit = count_names_administrators
                                                count_one_name = 0
                                                for name_administrator in names_administrators.split(','):
                                                    if count_one_name == limit:
                                                        receiver_administrator = name_administrator
                                                        break
                                                    else:
                                                        count_one_name = count_one_name + 1
                                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                             % (receiver_administrator) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                         The Budget <span style='font-weight: bold;'>%s</span> has been validated and awaits commercial approval</span>''' % (
                                                                 order.name) + ''' <br/>''' \
                                                             + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                         <br/><br/>'''
                                                email_id = self.env['mail.mail'].create(
                                                    {'subject': 'Quote N°' + str(
                                                        order.name) + ' Validated by Seller',
                                                     'email_from': self.env.user.partner_id.email,
                                                     'email_to': mail,
                                                     'message_type': 'email',
                                                     'body_html': email_body,
                                                     })
                                                email_id.send()
                                                count_names_administrators = count_names_administrators + 1

                                if order.company_id.sellers_notifications == 'enabled':
                                    if authorized_notifications_users:
                                        for au_user in authorized_notifications_users:
                                            if au_user.id == order.user_id.id:
                                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                             You have validated the Budget <span style='font-weight: bold;'>%s</span> and I await commercial approval</span>''' % (
                                                                 order.name) + ''' <br/>''' \
                                                             + '''<span style='font-style: 14px;'>You can see it by clicking</span> \
                                                                                                                                                                                                             <div style="margin-top:40px;">
                                                                                                                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                             font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                             <br/><br/>'''
                                                email_id = self.env['mail.mail'].create(
                                                    {'subject': 'Quote N°' + str(order.name) + ' Validated',
                                                     'email_from': self.env.user.partner_id.email,
                                                     'email_to': au_user.partner_id.email,
                                                     'message_type': 'email',
                                                     'body_html': email_body,
                                                     })
                                                email_id.send()

                                order.write({'state': 'draft_ok'})
                            else:
                                raise UserError(_('The total amount of the sales order is less than allowed, minimum: ' + str(round(order.company_id.commercial_approval_amount))))
                    else:
                        if general_language == 'es':
                            raise UserError(_('El usuario: ' + order.user_id.name + ', no tiene habilitado las notificaciones para vendedores.'))
                        else:
                            raise UserError(_('The user: ' + order.user_id.name + ', you don t have vendor notifications enabled.'))

    @api.multi
    def confirm_draft(self):
        for order in self:
            if order.state not in ['draft_ok']:
                continue
            else:
                if order.company_id.commercial_approval == 'disabled':
                    if order.company_id.financial_approval == 'disabled':
                        if order.company_id.creation_sale_orders_permits == 'disabled':
                            if order.company_id.generation_sales_invoices == 'disabled':
                                if order.company_id.validation_sales_invoices == 'disabled':
                                    raise UserError(_('at least one state must be enabled'))
                                elif order.company_id.validation_sales_invoices == 'enabled':
                                    return super(SaleOrder, self).action_confirm()
                            elif order.company_id.generation_sales_invoices == 'enabled':
                                return super(SaleOrder, self).action_confirm()
                        elif order.company_id.creation_sale_orders_permits  == 'enabled':
                            order.write({'state': 'financial_state'})
                    elif order.company_id.financial_approval == 'enabled':
                        order.write({'state': 'commercial_state'})
                elif order.company_id.commercial_approval == 'enabled':
                    authorized_commercial_group = self.env.ref('sale_order_status_approvals.commercial_approval_sale_orders_permits')
                    authorized_commercial_users = self.env['res.users'].search([('groups_id', '=', authorized_commercial_group.id)])
                    authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                    authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                    authorized_administrators_notifications_group = self.env.ref('sale_order_status_approvals.administrator_notifications_sales_orders_permits')
                    authorized_administrators_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_administrators_notifications_group.id)])
                    so_url = order._make_url('sale.order', order.id)
                    language = order.user_id.lang.split('_')
                    general_language = language[0]

                    if general_language == 'es':
                        if authorized_commercial_users:
                            for au_user in authorized_commercial_users:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                              El Presupuesto <span style='font-weight: bold;'>%s</span> Fue aprobado comercialmente y está esperando aprobación financiera.</span>''' % (order.name) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                             <div style="margin-top:40px;">
                                                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                             font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                             <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'Presupuesto N°' + str(order.name) + ' Listo con aprobación comercial',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()

                        if order.company_id.sellers_notifications == 'enabled':
                            if authorized_notifications_users:
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                         El Presupuesto N°<span style='font-weight: bold;'>%s</span> Fue aprobado comercialmente y está esperando aprobación financiera.</span>''' % (order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Puedes verlo haciendo click</span> \
                                                                                                                                                                 <div style="margin-top:40px;">
                                                                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                 font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                 <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' Listo con aprobación comercial',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()

                        if order.company_id.administrators_notifications == 'enabled':
                            if authorized_administrators_notifications_users:
                                for au_user in authorized_administrators_notifications_users:
                                    email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                 % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                  El Presupuesto <span style='font-weight: bold;'>%s</span> Fue aprobado comercialmente y está esperando aprobación financiera.</span>''' % (order.name) + ''' <br/>''' \
                                                 + '''<span style='font-style: 14px;'>Puedes verlo haciendo click</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Prespuesto</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                    email_id = self.env['mail.mail'].create(
                                        {'subject': 'Presupuesto N°' + str(order.name) + ' Listo con aprobación comercial',
                                         'email_from': self.env.user.partner_id.email,
                                         'email_to': au_user.partner_id.email,
                                         'message_type': 'email',
                                         'body_html': email_body,
                                         })
                                    email_id.send()
                    else:
                        if authorized_commercial_users:
                            for au_user in authorized_commercial_users:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                             The Budget <span style='font-weight: bold;'>%s</span> It was commercially approved and is awaiting financial approval.</span>''' % (
                                                 order.name) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                             <div style="margin-top:40px;">
                                                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                             font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                             <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'Quote N°' + str(order.name) + ' ready with Commercial Approval',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()

                        if order.company_id.sellers_notifications == 'enabled':
                            if authorized_notifications_users:
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                 The Budget <span style='font-weight: bold;'>%s</span> It was commercially approved and is awaiting financial approval.</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>You can see it by clicking</span> \
                                                                                                                                                                 <div style="margin-top:40px;">
                                                                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                 font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                 <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Quote N°' + str(order.name) + ' ready with Commercial Approval',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()

                        if order.company_id.administrators_notifications == 'enabled':
                            if authorized_administrators_notifications_users:
                                for au_user in authorized_administrators_notifications_users:
                                    email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                 % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                     The Budget <span style='font-weight: bold;'>%s</span> It was commercially approved and is awaiting financial approval.</span>''' % (
                                                     order.name) + ''' <br/>''' \
                                                 + '''<span style='font-style: 14px;'>You can see it by clicking</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                    email_id = self.env['mail.mail'].create(
                                        {'subject': 'Quote N°' + str(order.name) + ' ready with Commercial Approval',
                                         'email_from': self.env.user.partner_id.email,
                                         'email_to': au_user.partner_id.email,
                                         'message_type': 'email',
                                         'body_html': email_body,
                                         })
                                    email_id.send()

                    order.write({'state': 'commercial_state'})

    @api.multi
    def confirm_finan(self):
        for order in self:
            if order.state not in ['commercial_state']:
                continue
            else:
                if order.company_id.financial_approval == 'disabled':
                    if order.company_id.creation_sale_orders_permits == 'disabled':
                        if order.company_id.generation_sales_invoices == 'disabled':
                            if order.company_id.validation_sales_invoices == 'disabled':
                                raise UserError(_('at least one state must be enabled'))
                            elif order.company_id.validation_sales_invoices == 'enabled':
                                return super(SaleOrder, self).action_confirm()
                        elif order.company_id.generation_sales_invoices == 'enabled':
                            return super(SaleOrder, self).action_confirm()
                    elif order.company_id.creation_sale_orders_permits == 'enabled':
                        order.write({'state': 'financial_state'})
                elif order.company_id.financial_approval == 'enabled':
                    authorized_financial_group = self.env.ref('sale_order_status_approvals.financial_approval_sale_orders_permits')
                    authorized_financial_users = self.env['res.users'].search([('groups_id', '=', authorized_financial_group.id)])
                    authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                    authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                    authorized_administrators_notifications_group = self.env.ref('sale_order_status_approvals.administrator_notifications_sales_orders_permits')
                    authorized_administrators_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_administrators_notifications_group.id)])
                    so_url = order._make_url('sale.order', order.id)
                    language = order.user_id.lang.split('_')
                    general_language = language[0]

                    if general_language == 'es':
                        if authorized_financial_users:
                            for au_user in authorized_financial_users:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                              El Presupuesto <span style='font-weight: bold;'>%s</span> financieramente aprobado, puede hacer un seguimiento.</span>''' % (order.name) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                         <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'Presupuesto N°' + str(order.name) + ' listo con aprobación financiera',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()

                        if order.company_id.sellers_notifications == 'enabled':
                            if authorized_notifications_users:
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                       El Presupuesto N°<span style='font-weight: bold;'>%s</span> financieramente aprobado, puede hacer un seguimiento.</span>''' % (order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                 <div style="margin-top:40px;">
                                                                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                 font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                 <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' listo con aprobación financiera',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()

                        if order.company_id.administrators_notifications == 'enabled':
                            if authorized_administrators_notifications_users:
                                for au_user in authorized_administrators_notifications_users:
                                    email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                 % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                  El Presupuesto <span style='font-weight: bold;'>%s</span> financieramente aprobado, puede hacer un seguimiento.</span>''' % (order.name) + ''' <br/>''' \
                                                 + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                    email_id = self.env['mail.mail'].create(
                                        {'subject': 'Presupuesto N°' + str(order.name) + ' listo con aprobación financiera',
                                         'email_from': self.env.user.partner_id.email,
                                         'email_to': au_user.partner_id.email,
                                         'message_type': 'email',
                                         'body_html': email_body,
                                         })
                                    email_id.send()
                    else:
                        if authorized_financial_users:
                            for au_user in authorized_financial_users:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                         The Budget <span style='font-weight: bold;'>%s</span> financially approved, you can follow up</span>''' % (
                                                 order.name) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                         <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'Quote N°' + str(order.name) + ' ready with financial approval',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()

                        if order.company_id.sellers_notifications == 'enabled':
                            if authorized_notifications_users:
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                 The Budget <span style='font-weight: bold;'>%s</span> financially approved, you can follow up</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                 <div style="margin-top:40px;">
                                                                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                 font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                 <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Quote N°' + str(order.name) + ' ready with financial approval',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()

                        if order.company_id.administrators_notifications == 'enabled':
                            if authorized_administrators_notifications_users:
                                for au_user in authorized_administrators_notifications_users:
                                    email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                 % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                     The Budget <span style='font-weight: bold;'>%s</span> financially approved, you can follow up</span>''' % (
                                                     order.name) + ''' <br/>''' \
                                                 + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                    email_id = self.env['mail.mail'].create(
                                        {'subject': 'Quote N°' + str(order.name) + ' ready with financial approval',
                                         'email_from': self.env.user.partner_id.email,
                                         'email_to': au_user.partner_id.email,
                                         'message_type': 'email',
                                         'body_html': email_body,
                                         })
                                    email_id.send()

                    order.write({'state': 'financial_state'})

    @api.multi
    def confirm_sale_order(self):
        for order in self:
            if order.state not in ['financial_state']:
                continue
            else:
                if order.company_id.creation_sale_orders_permits == 'disabled':
                    if order.company_id.generation_sales_invoices == 'disabled':
                        if order.company_id.validation_sales_invoices == 'disabled':
                            raise UserError(_('at least one state must be enabled'))
                        elif order.company_id.validation_sales_invoices == 'enabled':
                            return super(SaleOrder, self).action_confirm()
                    elif order.company_id.generation_sales_invoices == 'enabled':
                        return super(SaleOrder, self).action_confirm()
                elif order.company_id.creation_sale_orders_permits == 'enabled':
                    authorized_create_sales_orders_group = self.env.ref('sale_order_status_approvals.creation_sale_orders_permits')
                    authorized_create_sales_orders_users = self.env['res.users'].search([('groups_id', '=', authorized_create_sales_orders_group.id)])
                    authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                    authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                    authorized_administrators_notifications_group = self.env.ref('sale_order_status_approvals.administrator_notifications_sales_orders_permits')
                    authorized_administrators_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_administrators_notifications_group.id)])
                    so_url = order._make_url('sale.order', order.id)
                    language = order.user_id.lang.split('_')
                    general_language = language[0]

                    if general_language == 'es':
                        if authorized_create_sales_orders_users:
                            for au_user in authorized_create_sales_orders_users:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                              El Presupuesto N°<span style='font-weight: bold;'>%s</span> se ha convertido en un Pedido de Venta, puede seguirlo.</span>''' % (order.name) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                         <div style="margin-top:40px;">
                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                         <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'Presupuesto N°' + str(order.name) + ' se ha convertido en Pedido de Venta',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()

                        if order.company_id.sellers_notifications == 'enabled':
                            if authorized_notifications_users:
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                      El Presupuesto N°<span style='font-weight: bold;'>%s</span> se ha convertido en un Pedido de Venta, puede seguirlo.</span>''' % (order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                             <div style="margin-top:40px;">
                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                             font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                             <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Presupuesto N°' + str(order.name) + ' se ha convertido en Pedido de Venta',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()

                        if order.company_id.administrators_notifications == 'enabled':
                            if authorized_administrators_notifications_users:
                                for au_user in authorized_administrators_notifications_users:
                                    email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                 % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                  El Presupuesto N°<span style='font-weight: bold;'>%s</span> se ha convertido en un Pedido de Venta, puede seguirlo.</span>''' % (order.name) + ''' <br/>''' \
                                                 + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                             <div style="margin-top:40px;">
                                                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                             font-size: 16px;" class="o_default_snippet_text">Ver Presupuesto</a></div>\
                                                                                                                                             <br/><br/>'''
                                    email_id = self.env['mail.mail'].create(
                                        {'subject': 'Presupuesto N°' + str(order.name) + ' se ha covertido en un Pedido de Ventas',
                                         'email_from': self.env.user.partner_id.email,
                                         'email_to': au_user.partner_id.email,
                                         'message_type': 'email',
                                         'body_html': email_body,
                                         })
                                    email_id.send()
                    else:
                        if authorized_create_sales_orders_users:
                            for au_user in authorized_create_sales_orders_users:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                         The Budget <span style='font-weight: bold;'>%s</span> has become a Sales Order, you can track it.</span>''' % (
                                                 order.name) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                         <div style="margin-top:40px;">
                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                         font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                         <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'Quote N°' + str(order.name) + ' has become a Sales Order',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()

                        if order.company_id.sellers_notifications == 'enabled':
                            if authorized_notifications_users:
                                for au_user in authorized_notifications_users:
                                    if au_user.id == order.user_id.id:
                                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                             The Budget <span style='font-weight: bold;'>%s</span> has become a Sales Order, you can track it.</span>''' % (
                                                         order.name) + ''' <br/>''' \
                                                     + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                             <div style="margin-top:40px;">
                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                             font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                             <br/><br/>'''
                                        email_id = self.env['mail.mail'].create(
                                            {'subject': 'Quote N°' + str(order.name) + ' has become a Sales Order',
                                             'email_from': self.env.user.partner_id.email,
                                             'email_to': au_user.partner_id.email,
                                             'message_type': 'email',
                                             'body_html': email_body,
                                             })
                                        email_id.send()

                        if order.company_id.administrators_notifications == 'enabled':
                            if authorized_administrators_notifications_users:
                                for au_user in authorized_administrators_notifications_users:
                                    email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                 % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                             The Budget <span style='font-weight: bold;'>%s</span> has become a Sales Order, you can track it.</span>''' % (
                                                     order.name) + ''' <br/>''' \
                                                 + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                             <div style="margin-top:40px;">
                                                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                             font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                             <br/><br/>'''
                                    email_id = self.env['mail.mail'].create(
                                        {'subject': 'Quote N°' + str(order.name) + ' has become a Sales Order',
                                         'email_from': self.env.user.partner_id.email,
                                         'email_to': au_user.partner_id.email,
                                         'message_type': 'email',
                                         'body_html': email_body,
                                         })
                                    email_id.send()

                    return super(SaleOrder, self).action_confirm()

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}

        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
            for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                elif line.qty_to_invoice < 0 and final:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order


            if order.company_id.generation_sales_invoices == 'disabled':
                if order.company_id.validation_sales_invoices == 'disabled':
                    raise UserError(_('at least one state must be enabled'))
                elif order.company_id.validation_sales_invoices == 'enabled':
                    order.write({'state': 'invoiced'})
                # raise UserError(_('at least one state must be enabled'))
            elif order.company_id.generation_sales_invoices == 'enabled':
                authorized_invoice_group = self.env.ref('sale_order_status_approvals.generation_sales_invoices_permits')
                authorized_invoice_users = self.env['res.users'].search([('groups_id', '=', authorized_invoice_group.id)])
                authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
                authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
                authorized_administrators_notifications_group = self.env.ref('sale_order_status_approvals.administrator_notifications_sales_orders_permits')
                authorized_administrators_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_administrators_notifications_group.id)])
                so_url = order._make_url('sale.order', order.id)
                language = order.user_id.lang.split('_')
                general_language = language[0]

                if general_language == 'es':
                    if authorized_invoice_users:
                        for au_user in authorized_invoice_users:
                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                          El Pedido de Venta N°<span style='font-weight: bold;'>%s</span> ha sido facturado, el documento generado a partir de este pedido está en forma de borrador para confirmar.</span>''' % (order.name) + ''' <br/>''' \
                                         + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                 <div style="margin-top:40px;">
                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                 font-size: 16px;" class="o_default_snippet_text">Ver Pedido de Venta</a></div>\
                                                                                                                 <br/><br/>'''
                            email_id = self.env['mail.mail'].create(
                                {'subject': 'Pedido de Venta N°' + str(order.name) + ' Facturado',
                                 'email_from': self.env.user.partner_id.email,
                                 'email_to': au_user.partner_id.email,
                                 'message_type': 'email',
                                 'body_html': email_body,
                                 })
                            email_id.send()

                    if order.company_id.sellers_notifications == 'enabled':
                        if authorized_notifications_users:
                            for au_user in authorized_notifications_users:
                                if au_user.id == order.user_id.id:
                                    email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                                 % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                  El Pedido de Venta N°<span style='font-weight: bold;'>%s</span> ha sido facturado, el documento generado a partir de este pedido está en forma de borrador para confirmar.</span>''' % (order.name) + ''' <br/>''' \
                                                 + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Pedido de Venta</a></div>\
                                                                                                                                                                                                                     <br/><br/>'''
                                    email_id = self.env['mail.mail'].create(
                                        {'subject': 'Pedido de Venta N°' + str(order.name) + ' Facturado',
                                         'email_from': self.env.user.partner_id.email,
                                         'email_to': au_user.partner_id.email,
                                         'message_type': 'email',
                                         'body_html': email_body,
                                         })
                                    email_id.send()

                    if order.company_id.administrators_notifications == 'enabled':
                        if authorized_administrators_notifications_users:
                            for au_user in authorized_administrators_notifications_users:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estimad@, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                              El Pedido de Venta N°<span style='font-weight: bold;'>%s</span> ha sido facturado, el documento generado a partir de este pedido está en forma de borrador para confirmar.</span>''' % (order.name) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Acceda haciendo click</span> \
                                                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">Ver Pedido de Venta</a></div>\
                                                                                                                                                                                                                                                     <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'Pedido de Venta N°' + str(order.name) + ' Facturado',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()
                else:
                    if authorized_invoice_users:
                        for au_user in authorized_invoice_users:
                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                 The Sales Order <span style='font-weight: bold;'>%s</span> has been invoiced, the document generated from this order is in draft form to confirm.</span>''' % (
                                             order.name) + ''' <br/>''' \
                                         + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                 <div style="margin-top:40px;">
                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                 font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                 <br/><br/>'''
                            email_id = self.env['mail.mail'].create(
                                {'subject': 'Sales Order N°' + str(order.name) + ' Invoiced',
                                 'email_from': self.env.user.partner_id.email,
                                 'email_to': au_user.partner_id.email,
                                 'message_type': 'email',
                                 'body_html': email_body,
                                 })
                            email_id.send()

                    if order.company_id.sellers_notifications == 'enabled':
                        if authorized_notifications_users:
                            for au_user in authorized_notifications_users:
                                if au_user.id == order.user_id.id:
                                    email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                                 % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                     The Sales Order <span style='font-weight: bold;'>%s</span> has been invoiced, the document generated from this order is in draft form to confirm.</span>''' % (
                                                     order.name) + ''' <br/>''' \
                                                 + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                     <br/><br/>'''
                                    email_id = self.env['mail.mail'].create(
                                        {'subject': 'Sales Order N°' + str(order.name) + ' Invoiced',
                                         'email_from': self.env.user.partner_id.email,
                                         'email_to': au_user.partner_id.email,
                                         'message_type': 'email',
                                         'body_html': email_body,
                                         })
                                    email_id.send()

                    if order.company_id.administrators_notifications == 'enabled':
                        if authorized_administrators_notifications_users:
                            for au_user in authorized_administrators_notifications_users:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                                                                     The Sales Order <span style='font-weight: bold;'>%s</span> has been invoiced, the document generated from this order is in draft form to confirm.</span>''' % (
                                                 order.name) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                                                                     <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'Sales Order N°' + str(order.name) + ' Invoiced',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()

                order.write({'state': 'invoiced'})

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'origin': ', '.join(invoices_origin[group_key])})

        if not invoices:
            raise UserError(_('There is no invoiceable line.'))

        for invoice in invoices.values():
            invoice.compute_taxes()
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_total < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post_with_view('mail.message_origin_link',
                values={'self': invoice, 'origin': references[invoice]},
                subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]