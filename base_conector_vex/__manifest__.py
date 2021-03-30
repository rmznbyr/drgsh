# -*- coding: utf-8 -*-
{
    'name': "Multi Base Vex Connector",
    'summary': """
      Base Vex Connector """,

    'description': """
        Base Vex Connector
    """,
    'author': "Vex Soluciones",
    'website': "https://www.pasarelasdepagos.com/",

    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base','stock','website', 'website_sale','contacts','sale_management','delivery','website_sale_coupon'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/vex_product_template.xml',
        'views/vex_product_product.xml',
        'views/mensajes.xml',
        'views/customer.xml',
        'views/vex_instance.xml',
        'views/vex_order.xml',
        'views/vex_list.xml',
        'views/vex_logs.xml',
        'views/atributos.xml',
        'wizard/vex_synchro.xml',
        'data/vex_cron.xml',
        'data/product.xml'
    ],

    #'images': ['static/description/odoo-woo.gif'],
}