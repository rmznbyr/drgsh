# -*- coding: utf-8 -*-
# LGPL-3
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    website_ids = fields.Many2many(
        'website',
        string="Websites",
        help="""Add here all the websites on which you want to show this product
        leave it empty if you want to show the product in all websites.
        """)
