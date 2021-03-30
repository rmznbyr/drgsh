from odoo import api, fields, models


class Orders(models.Model):
    _inherit = 'sale.order'
    _description = "Ordenes de mercado libre"

    id_vex   = fields.Char(string="Connector ID")
    conector = fields.Selection([])
    server_vex = fields.Many2one('vex.instance')
    _sql_constraints = [
        ('unique_id_order_woo', 'unique(id_vex, server_vex , conector)', 'There can be no duplication of synchronized Orders')
    ]

