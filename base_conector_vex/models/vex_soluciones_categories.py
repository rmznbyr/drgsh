from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError


class Categories(models.Model):
    _inherit = 'product.public.category'
    id_vex = fields.Char(string="Id Connector")
    server_vex = fields.Many2one('vex.instance')
    conector = fields.Selection([])
    _sql_constraints = [
        ('unique_id_cat_woo', 'unique(id_vex, conector , server_vex)','There can be no duplication of synchronized categories')
    ]