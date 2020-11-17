# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Status Approvals",

    'summary': 'This Module adds new statuses to the sales order, each one with its approval validation',

    'description': """
        This Module adds new states to the sales order, each with its own validation to be approved,
         creating specific groups for the corresponding users that validate each one of the states.
         Also while the sales order progresses between each of the states, mailings are generated
         notifying the respective users involved.
    """,

    'author': "Felipe Soto",
    'website': "https://www.linkedin.com/in/felipe-soto-0642b745",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Generic Modules/Sales Management',
    'version': '1.6',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'sale', 'account', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/inherit_security.xml',
        'views/inherit_res_config_settings_notifications_views.xml',
        'views/inherit_res_config_settings_administrators_notifications_views.xml',
        'views/inherit_res_config_settings_commercial_views.xml',
        'views/inherit_res_config_settings_financial_views.xml',
        'views/inherit_res_config_settings_create_sales_orders_views.xml',
        'views/inherit_res_config_settings_generations_sales_invoices_views.xml',
        'views/inherit_res_config_settings_validated_sales_invoices_views.xml',
        'data/inherit_hr_data.xml',
        'views/inherit_sale_order.xml',
        'views/inherit_account_invoice_validate.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price':35.0,
    'currency':'EUR',
}