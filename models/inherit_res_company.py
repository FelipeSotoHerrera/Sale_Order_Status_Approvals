# -*- coding: utf-8 -*-

from odoo import fields, models

class Company(models.Model):
    _inherit = 'res.company'

    sellers_notifications = fields.Selection([
        ('disabled', 'Status notifications for vendors disabled'),
        ('enabled', 'Status notifications for sellers are triggered')
        ], string="Sellers Notifications", default='disabled',
        help="Enable budget status notifications via mail for sellers")

    commercial_approval = fields.Selection([
        ('disabled', 'Commercial Approval for Disabled Sales Order'),
        ('enabled', 'Commercial Approval for the Sales Order Enabled')
        ], string="commercial approval", default='disabled',
        help="Enables the commercial approval status to limit and review the sales order confirmation process")

    commercial_approval_amount = fields.Float(string='commercial approval validation Amount', default=75000,
        help="Minimum quantity from which commercial approval is required")

    financial_approval = fields.Selection([
        ('disabled', 'Financial Approval for Disabled Sales Order'),
        ('enabled', 'Financial Approval for the Sales Order Enabled')
        ], string="financial approval", default='disabled',
        help="Enables the financial approval status to limit and review the sales order confirmation process")

    creation_sale_orders_permits = fields.Selection([
        ('disabled', 'creation sale orders permits for Disabled Sales Order'),
        ('enabled', 'creation sale orders permits for the Sales Order Enabled')
        ], string="creation sale orders permits", default='disabled',
        help="Enables the creation sale orders status to limit and review the sales order confirmation process")

    generation_sales_invoices = fields.Selection([
        ('disabled', 'generation sales invoices permits for Disabled Sales Order'),
        ('enabled', 'generation sales invoices permits for the Sales Order Enabled')
        ], string="generation sales invoices permits", default='disabled',
        help="Allows notification of the sales order status to be invoiced when generating the sales invoice draft")

    administrators_notifications = fields.Selection([
        ('disabled', 'Status notifications for administrators disabled'),
        ('enabled', 'Status notifications for administrators are triggered')
        ], string="Administrators Notifications", default='disabled',
        help="Enable budget status notifications via mail for Administrators")

    validation_sales_invoices = fields.Selection([
        ('disabled', 'validation sales invoices permits for Disabled Sales Order'),
        ('enabled', 'validation sales invoices permits for the Sales Order Enabled')
        ], string="validation sales invoices permits", default='disabled',
        help="Allows the validation of the draft sales invoice to notify that it has been validated")