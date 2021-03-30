from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError

class Customers(models.Model):
    _inherit         = 'res.partner'
    _description     = "Clientes de mercado Libre"
    conector         = fields.Selection(selection_add=[('meli', 'Mercado Libre')])
    id_customer     = fields.Char(string="Customer ID")
    nickname        = fields.Char(string="Customer Nickname")
    conector = fields.Selection(selection_add=[('meli', 'Mercado Libre')])