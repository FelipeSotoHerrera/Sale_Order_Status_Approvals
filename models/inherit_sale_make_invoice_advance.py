# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            sale_orders.action_invoice_create()
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                else:
                    tax_ids = taxes.ids
                context = {'lang': order.partner_id.lang}
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, tax_ids)],
                    'is_downpayment': True,
                })
                del context

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
                                              El Pedido de Venta N°<span style='font-weight: bold;'>%s</span> ha sido facturado, el documento generado a partir de este pedido está en forma de borrador para confirmar.</span>''' % (
                                                 order.name) + ''' <br/>''' \
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
                                                      El Pedido de Venta N°<span style='font-weight: bold;'>%s</span> ha sido facturado, el documento generado a partir de este pedido está en forma de borrador para confirmar.</span>''' % (
                                                         order.name) + ''' <br/>''' \
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
                                                  El Pedido de Venta N°<span style='font-weight: bold;'>%s</span> ha sido facturado, el documento generado a partir de este pedido está en forma de borrador para confirmar.</span>''' % (
                                                     order.name) + ''' <br/>''' \
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

                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
