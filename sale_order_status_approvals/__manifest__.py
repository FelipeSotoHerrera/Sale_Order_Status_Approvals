# -*- coding: utf-8 -*-
{
    'name': "Sale Order Status Approvals",

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
    'version': '1.0',

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
    'currency': 'EUR',
    "images": ['static/description/Banner.png'],
}

#### HISTORY ####

# VERSION - 0.1.0 [2020-11-19]
# Description Index modification, icon and banner images modified.

# VERSION - 0.0.9 [2020-11-18]
# Modification in manifest added line to raise banner, update of records and version.

# VERSION - 0.0.8 [2020-11-18]
# Icon change and banner added for Odoo Apps Store.

# VERSION - 0.0.7 [2020-11-18]
# extra line removal in index.

# VERSION - 0.0.6 [2020-11-17]
# Description Index modification, to improve image visualization.

# VERSION - 0.0.5 [2020-11-16]
# Added license and reading files, more modifying version of the module.

# VERSION - 0.0.4 [2020-11-16]
# Module folder restructuring.

# VERSION - 0.0.3 [2020-11-15]
# Index File cleanup in description.

# VERSION - 0.0.2 [2020-11-14]
# Modification in translation file, dependency was added to hr in manifest, icon and module description folder plus images were added.

# VERSION - 0.0.1 [2020-11-09]
# Initial release