from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError

class Attributes(models.Model):
    _inherit             = 'product.attribute'
    #id_product          = fields.Char(string="Product ID")
    conector = fields.Selection(selection_add=[('meli', 'Mercado Libre')])


class TerminosAtributos(models.Model):
    _inherit            = 'product.attribute.value'
    conector            = fields.Selection(selection_add=[('meli', 'Mercado Libre')])
