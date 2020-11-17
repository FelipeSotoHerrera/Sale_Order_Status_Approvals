# -*- coding: utf-8 -*-

import json
import re
import uuid
from functools import partial

from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode

from odoo import api, exceptions, fields, models, _
from odoo.tools import float_is_zero, float_compare, pycompat
from odoo.tools.misc import formatLang

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons import decimal_precision as dp
import logging

class SaleInvoiceValidated(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def _make_url(self, model, id):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url', default='http://localhost:8069')
        if base_url:
            base_url += '/web/login?db=%s&login=%s&key=%s#id=%s&model=%s' % (self._cr.dbname, '', '', id, model)
        return base_url

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead."))

        # if to_open_invoices.company_id.validation_sales_invoices == 'disabled':
        #     order.write({'state': 'invoiced'})
        #     # raise UserError(_('at least one state must be enabled'))
        # elif to_open_invoices.company_id.validation_sales_invoices == 'enabled':

        if to_open_invoices.company_id.validation_sales_invoices == 'enabled':
            authorized_invoice_group = self.env.ref('sale_order_status_approvals.validation_sales_invoices_permits')
            authorized_invoice_users = self.env['res.users'].search([('groups_id', '=', authorized_invoice_group.id)])
            authorized_notifications_group = self.env.ref('sale_order_status_approvals.sellers_notifications_sale_orders_permits')
            authorized_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_notifications_group.id)])
            authorized_administrators_notifications_group = self.env.ref('sale_order_status_approvals.administrator_notifications_sales_orders_permits')
            authorized_administrators_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_administrators_notifications_group.id)])
            so_url = to_open_invoices._make_url('account.invoice', to_open_invoices.id)
            language = to_open_invoices.user_id.lang.split('_')
            general_language = language[0]
            # to_open_invoices.user_id.lang
            # to_open_invoices.user_id.id
            # au_user.id

            if general_language == 'es':
                if authorized_invoice_users:
                    for au_user in authorized_invoice_users:
                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estiamd@, %s</span>''' \
                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                      La Factura <span style='font-weight: bold;'>%s</span> ha sido confirmada y Validada.</span>''' % (
                                         to_open_invoices.next_invoice_number) + ''' <br/>''' \
                                     + '''<span style='font-style: 14px;'>Acceda haciendo clic</span> \
                                                                                                             <div style="margin-top:40px;">
                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                             font-size: 16px;" class="o_default_snippet_text">Ver Factura</a></div>\
                                                                                                             <br/><br/>'''
                        email_id = self.env['mail.mail'].create(
                            {'subject': 'Factura N°' + str(to_open_invoices.next_invoice_number) + ' confirmada y validada',
                             'email_from': self.env.user.partner_id.email,
                             'email_to': au_user.partner_id.email,
                             'message_type': 'email',
                             'body_html': email_body,
                             })
                        email_id.send()

                if to_open_invoices.company_id.sellers_notifications == 'enabled':
                    if authorized_notifications_users:
                        for au_user in authorized_notifications_users:
                            if au_user.id == to_open_invoices.user_id.id:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estiamd@, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                      La Factura <span style='font-weight: bold;'>%s</span> ha sido confirmada y Validada.</span>''' % (
                                                 to_open_invoices.next_invoice_number) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Acceda haciendo clic</span> \
                                                                                                                                             <div style="margin-top:40px;">
                                                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                             font-size: 16px;" class="o_default_snippet_text">Ver Factura</a></div>\
                                                                                                                                             <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'Factura N°' + str(to_open_invoices.next_invoice_number) + ' confirmada y validada',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()

                if to_open_invoices.company_id.administrators_notifications == 'enabled':
                    if authorized_administrators_notifications_users:
                        for au_user in authorized_administrators_notifications_users:
                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Estiamd@, %s</span>''' \
                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                  La Factura <span style='font-weight: bold;'>%s</span> ha sido confirmada y Validada.</span>''' % (
                                             to_open_invoices.next_invoice_number) + ''' <br/>''' \
                                         + '''<span style='font-style: 14px;'>Acceda haciendo clic</span> \
                                                                                                                                         <div style="margin-top:40px;">
                                                                                                                                         <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                         padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                         font-size: 16px;" class="o_default_snippet_text">Ver Factura</a></div>\
                                                                                                                                         <br/><br/>'''
                            email_id = self.env['mail.mail'].create(
                                {'subject': 'Factura N°' + str(
                                    to_open_invoices.next_invoice_number) + ' confirmada y validada',
                                 'email_from': self.env.user.partner_id.email,
                                 'email_to': au_user.partner_id.email,
                                 'message_type': 'email',
                                 'body_html': email_body,
                                 })
                            email_id.send()

                    # order.write({'state': 'invoiced'})
            else:
                if authorized_invoice_users:
                    for au_user in authorized_invoice_users:
                        email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                     % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                             The Invoice <span style='font-weight: bold;'>%s</span> has been confirmed and validated.</span>''' % (
                                         to_open_invoices.next_invoice_number) + ''' <br/>''' \
                                     + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                             <div style="margin-top:40px;">
                                                                                                             <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                             padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                             font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                             <br/><br/>'''
                        email_id = self.env['mail.mail'].create(
                            {'subject': 'The Invoice N°' + str(
                                to_open_invoices.next_invoice_number) + ' confirmed and validated',
                             'email_from': self.env.user.partner_id.email,
                             'email_to': au_user.partner_id.email,
                             'message_type': 'email',
                             'body_html': email_body,
                             })
                        email_id.send()

                if to_open_invoices.company_id.sellers_notifications == 'enabled':
                    if authorized_notifications_users:
                        for au_user in authorized_notifications_users:
                            if au_user.id == to_open_invoices.user_id.id:
                                email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                             % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                     The Invoice <span style='font-weight: bold;'>%s</span> has been confirmed and validated.</span>''' % (
                                                 to_open_invoices.next_invoice_number) + ''' <br/>''' \
                                             + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                     <div style="margin-top:40px;">
                                                                                                                                                                                                     <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                     padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                     font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                     <br/><br/>'''
                                email_id = self.env['mail.mail'].create(
                                    {'subject': 'The Invoice N°' + str(
                                        to_open_invoices.next_invoice_number) + ' confirmed and validated',
                                     'email_from': self.env.user.partner_id.email,
                                     'email_to': au_user.partner_id.email,
                                     'message_type': 'email',
                                     'body_html': email_body,
                                     })
                                email_id.send()

                if to_open_invoices.company_id.administrators_notifications == 'enabled':
                    if authorized_administrators_notifications_users:
                        for au_user in authorized_administrators_notifications_users:
                            email_body = ''' <span style='font-style: 16px;font-weight: bold;'>Dear, %s</span>''' \
                                         % (au_user.name) + ''' <br/><br/>''' + ''' <span style='font-style: 14px;'> \
                                                                                                                                                                                                 The Invoice <span style='font-weight: bold;'>%s</span> has been confirmed and validated.</span>''' % (
                                             to_open_invoices.next_invoice_number) + ''' <br/>''' \
                                         + '''<span style='font-style: 14px;'>Please access by clicking</span> \
                                                                                                                                                                                                 <div style="margin-top:40px;">
                                                                                                                                                                                                 <a href="''' + so_url + '''" style="background-color: #1abc9c; \
                                                                                                                                                                                                 padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; \
                                                                                                                                                                                                 font-size: 16px;" class="o_default_snippet_text">See Budget</a></div>\
                                                                                                                                                                                                 <br/><br/>'''
                            email_id = self.env['mail.mail'].create(
                                {'subject': 'The Invoice N°' + str(
                                    to_open_invoices.next_invoice_number) + ' confirmed and validated',
                                 'email_from': self.env.user.partner_id.email,
                                 'email_to': au_user.partner_id.email,
                                 'message_type': 'email',
                                 'body_html': email_body,
                                 })
                            email_id.send()

                    # order.write({'state': 'invoiced'})

        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()

    def action_invoice_cancel(self):

        sale_order_id = self.env['sale.order'].search([('name', '=', self.origin)])

        sale_order_id.write({'state': 'sale'})

        return super(SaleInvoiceValidated, self).action_invoice_cancel()