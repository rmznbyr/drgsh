from odoo import api, fields, models

class Logs(models.Model):
    _inherit = 'vex.logs'
    server_vex = fields.Many2one('vex.instance')
    conector = fields.Selection(selection_add=[('meli', 'Mercado Libre')])
    
