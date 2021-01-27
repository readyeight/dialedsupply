# -*- coding: utf-8 -*-
{
    'name': "Vendor Mapping Table",
    'summary': """
        Vendor Mapping Table""",
    'description': """
        Vendor Mapping Table
    """,
    'author': "Silverdaletech",
    'company': 'Silverdaletech',
    'website': "https://www.silverdaletech.com/",
    'category': 'website',
    'version': '13.0.1.0',
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/vendor_mapping.xml',
        'views/res_partner.xml',
        'data/mapping_demo.xml'
    ],
    'demo': [
        # 'data/mapping_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}