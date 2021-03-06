# -*- coding: utf-8 -*-
{
    'name': "HydroFarm Integration",
    'version': '14.0.2103',
    'author': 'silverdaletech',
    'website': 'www.silverdaletech.com',
    'description': 'HydroFarm integration',
    'author': "Silverdaletech",
    'category': 'Product',
    'depends': ['base', 'sale', 'vendor_mapping'],
    'data': [

        'data/cron_data.xml',

        'security/hydrofarm_product_security.xml',
        'security/ir.model.access.csv',

        'views/hydrofarm_vendor_view.xml',

        'wizard/import_wizard.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
