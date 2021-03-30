from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError

class Attributes(models.Model):
    _inherit            = 'product.attribute'
    id_vex              = fields.Char(string="Connector ID")
    conector = fields.Selection([])
    server_vex = fields.Many2one('vex.instance')

class TerminosAtributos(models.Model):
    _inherit            = 'product.attribute.value'
    id_vex              = fields.Char(string="Meli ID")
    conector = fields.Selection([])
    server_vex = fields.Many2one('vex.instance')