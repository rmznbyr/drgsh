from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError

class Categories(models.Model):
    _inherit                = 'product.public.category'
    conector                = fields.Selection(selection_add=[('meli', 'Mercado Libre')])
    '''
    _sql_constraints = [
        ('unique_id_cat_meli', 'unique(id_app, server_meli)', 'There can be no duplication of synchronized categories')
    ]
    '''