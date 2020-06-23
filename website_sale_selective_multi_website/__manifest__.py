# -*- encoding: utf-8 -*-
# LGPL-3
{
    'name': 'Multiple Websites per Product',
    'category': 'Website',
    'sequence': 55,
    'summary': 'Add multiple websites per product in Odoo multi website',
    'website': 'https://oopo.io',
    'version': '13.0.0.0.3',
    'license': 'LGPL-3',
    'author': 'Oopo.io',
    'depends': [
        'website_sale',
    ],
    'installable': True,
    'data': [
        'views/product_view.xml',
    ],
    'demo': [
    ],
    'images': [
        'static/description/cover.png',
    ],
    'qweb': [],
    'application': True,
    'price': 79,
    'currency': 'EUR',
}
