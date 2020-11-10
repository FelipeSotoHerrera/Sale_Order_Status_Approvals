# -*- coding: utf-8 -*-
from odoo.tools import pycompat
from odoo.tools.translate import _
import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from collections import defaultdict

USER_PRIVATE_FIELDS = ['password']

class InheritResUsers(models.Model):
    _inherit = 'res.users'
    __uid_cache = defaultdict(dict)

    mail_administrators_notifications = fields.Char('Mail Administrators Notifications', help='mailing list for notification of administrators.')
    mail_commercial_notifications = fields.Char('Mail Commercial Notifications', help='mailing list for notification of Commercial Aprove.')
    names_administrators_notifications = fields.Char('Name Administrators Notifications', help='names list for notification of administrators.')
    names_commercial_notifications = fields.Char('Name Commercial Notifications', help='names list for notification of Commercial Aprove.')

    @api.model
    def create(self, vals):
        authorized_commercial_group = self.env.ref('sale_order_status_approvals.commercial_approval_sale_orders_permits')
        authorized_commercial_users = self.env['res.users'].search([('groups_id', '=', authorized_commercial_group.id)])
        authorized_administrators_notifications_group = self.env.ref('sale_order_status_approvals.administrator_notifications_sales_orders_permits')
        authorized_administrators_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_administrators_notifications_group.id)])
        mail_commercial_notifications_values = ''
        mail_administrators_notifications_values = ''
        name_commercial_notifications_values = ''
        name_administrators_notifications_values = ''
        user = super(InheritResUsers, self).create(vals)
        user.partner_id.active = user.active
        if user.partner_id.company_id:
            user.partner_id.write({'company_id': user.company_id.id})

        for au_user in authorized_commercial_users:
            if mail_commercial_notifications_values == '':
                mail_commercial_notifications_values = au_user.partner_id.email + ','
                name_commercial_notifications_values = au_user.partner_id.display_name + ','
            else:
                mail_commercial_notifications_values = mail_commercial_notifications_values + au_user.partner_id.email + ','
                name_commercial_notifications_values = name_commercial_notifications_values + au_user.partner_id.display_name + ','

        for au_user in authorized_administrators_notifications_users:
            if mail_administrators_notifications_values == '':
                mail_administrators_notifications_values = au_user.partner_id.email + ','
                name_administrators_notifications_values = au_user.partner_id.display_name + ','
            else:
                mail_administrators_notifications_values = mail_administrators_notifications_values + au_user.partner_id.email + ','
                name_administrators_notifications_values = name_administrators_notifications_values + au_user.partner_id.display_name + ','

        user.write({'mail_commercial_notifications': mail_commercial_notifications_values})
        user.write({'mail_administrators_notifications': mail_administrators_notifications_values})
        user.write({'names_commercial_notifications': name_commercial_notifications_values})
        user.write({'names_administrators_notifications': name_administrators_notifications_values})


        return user

    @api.multi
    def write(self, values):
        if values.get('active') == False:
            for user in self:
                if user.id == SUPERUSER_ID:
                    raise UserError(_("You cannot deactivate the admin user."))
                elif user.id == self._uid:
                    raise UserError(_("You cannot deactivate the user you're currently logged in as."))

        if self == self.env.user:
            for key in list(values):
                if not (key in self.SELF_WRITEABLE_FIELDS or key.startswith('context_')):
                    break
            else:
                if 'company_id' in values:
                    if values['company_id'] not in self.env.user.company_ids.ids:
                        del values['company_id']
                # safe fields only, so we write as super-user to bypass access rights
                self = self.sudo()

        self.set_commercial_approval_mails(values)
        self.set_administrators_notifications_mails(values)

        res = super(InheritResUsers, self).write(values)
        if 'company_id' in values:
            for user in self:
                # if partner is global we keep it that way
                if user.partner_id.company_id and user.partner_id.company_id.id != values['company_id']:
                    user.partner_id.write({'company_id': user.company_id.id})
            # clear default ir values when company changes
            self.env['ir.default'].clear_caches()

        # clear caches linked to the users
        if 'groups_id' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
            self.has_group.clear_cache(self)
        if any(key.startswith('context_') or key in ('lang', 'tz') for key in values):
            self.context_get.clear_cache(self)
        if any(key in values for key in ['active'] + USER_PRIVATE_FIELDS):
            db = self._cr.dbname
            for id in self.ids:
                self.__uid_cache[db].pop(id, None)
        if any(key in values for key in self._get_session_token_fields()):
            self._invalidate_session_cache()

        return res

    @api.multi
    def set_commercial_approval_mails(self, values):
        authorized_commercial_group = self.env.ref('sale_order_status_approvals.commercial_approval_sale_orders_permits')
        authorized_commercial_users = self.env['res.users'].search([('groups_id', '=', authorized_commercial_group.id)])
        mail_commercial_notifications_values = ''
        name_commercial_notifications_values = ''

        for au_user in authorized_commercial_users:
            if mail_commercial_notifications_values == '':
                mail_commercial_notifications_values = au_user.partner_id.email + ','
                name_commercial_notifications_values = au_user.partner_id.display_name + ','
            else:
                mail_commercial_notifications_values = mail_commercial_notifications_values + au_user.partner_id.email + ','
                name_commercial_notifications_values = name_commercial_notifications_values + au_user.partner_id.display_name + ','

        if mail_commercial_notifications_values != '':
            values['mail_commercial_notifications'] = mail_commercial_notifications_values
            values['names_commercial_notifications'] = name_commercial_notifications_values


    @api.multi
    def set_administrators_notifications_mails(self, values):
        authorized_administrators_notifications_group = self.env.ref('sale_order_status_approvals.administrator_notifications_sales_orders_permits')
        authorized_administrators_notifications_users = self.env['res.users'].search([('groups_id', '=', authorized_administrators_notifications_group.id)])
        mail_administrators_notifications_values = ''
        name_administrators_notifications_values = ''

        for au_user in authorized_administrators_notifications_users:
            if mail_administrators_notifications_values == '':
                mail_administrators_notifications_values = au_user.partner_id.email + ','
                name_administrators_notifications_values = au_user.partner_id.display_name + ','
            else:
                mail_administrators_notifications_values = mail_administrators_notifications_values + au_user.partner_id.email + ','
                name_administrators_notifications_values = name_administrators_notifications_values + au_user.partner_id.display_name + ','

        if mail_administrators_notifications_values != '':
            values['mail_administrators_notifications'] = mail_administrators_notifications_values
            values['names_administrators_notifications'] = name_administrators_notifications_values