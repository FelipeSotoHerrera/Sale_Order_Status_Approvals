# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import api, fields, models


class InheritResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sellers_notifications_verify = fields.Boolean(string="sellers notifications", default=lambda self: self.env.user.company_id.sellers_notifications == 'enabled')
    sellers_notifications = fields.Selection(related='company_id.sellers_notifications', string="Sellers Notifications *")

    permits_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True, help='Field created to index the minimum amount of currency for commercial approval')
    commercial_approval_verify = fields.Boolean(string="commercial approval", default=lambda self: self.env.user.company_id.commercial_approval == 'enabled')
    commercial_approval = fields.Selection(related='company_id.commercial_approval', string="commercial approval *")
    commercial_approval_amount = fields.Float(related='company_id.commercial_approval_amount', string="Minimum Amount", currency_field='permits_currency_id')

    financial_approval_verify = fields.Boolean(string="financial approval", default=lambda self: self.env.user.company_id.financial_approval == 'enabled')
    financial_approval = fields.Selection(related='company_id.financial_approval', string="financial approval *")

    creation_sale_orders_permits_verify = fields.Boolean(string="creation sale orders permits", default=lambda self: self.env.user.company_id.creation_sale_orders_permits == 'enabled')
    creation_sale_orders_permits = fields.Selection(related='company_id.creation_sale_orders_permits', string="creation sale orders permits *")

    generation_sales_invoices_verify = fields.Boolean(string="generation sales invoices", default=lambda self: self.env.user.company_id.generation_sales_invoices == 'enabled')
    generation_sales_invoices = fields.Selection(related='company_id.generation_sales_invoices', string="generation sales invoices *")

    administrators_notifications_verify = fields.Boolean(string="administrators notifications", default=lambda self: self.env.user.company_id.administrators_notifications == 'enabled')
    administrators_notifications = fields.Selection(related='company_id.administrators_notifications', string="Administrators Notifications *")

    validation_sales_invoices_verify = fields.Boolean(string="validation sales invoices", default=lambda self: self.env.user.company_id.validation_sales_invoices == 'enabled')
    validation_sales_invoices = fields.Selection(related='company_id.validation_sales_invoices', string="validation sales invoices *")

    def set_values(self):
        super(InheritResConfigSettings, self).set_values()
        self.sellers_notifications = 'enabled' if self.sellers_notifications_verify else 'disabled'
        self.commercial_approval = 'enabled' if self.commercial_approval_verify else 'disabled'
        self.financial_approval = 'enabled' if self.financial_approval_verify else 'disabled'
        self.creation_sale_orders_permits = 'enabled' if self.creation_sale_orders_permits_verify else 'disabled'
        self.generation_sales_invoices = 'enabled' if self.generation_sales_invoices_verify else 'disabled'
        self.administrators_notifications = 'enabled' if self.administrators_notifications_verify else 'disabled'
        self.validation_sales_invoices = 'enabled' if self.validation_sales_invoices_verify else 'disabled'