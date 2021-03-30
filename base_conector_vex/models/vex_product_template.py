# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
from woocommerce import API

_logger = logging.getLogger(__name__)


import requests
import base64

class Product(models.Model):
    _name                  = 'product.template'
    _inherit               = 'product.template'
    id_vex                 = fields.Char(string="Connector  ID")
    server_vex = fields.Many2one('vex.instance')
    conector               = fields.Selection([])
    edit_id                = fields.Boolean(default=False)
    permalink              = fields.Char()
    img_url_vex            = fields.Char('Imagen Url')
    _sql_constraints = [
        ('unique_id_prod_vex', 'unique(id_vex, conector, server_vex)',
         'There can be no duplication of synchronized Products Template')
    ]
    '''
    @api.onchange('img_url_vex')
    def change_image_vex(self):
        for record in self:
            image = None
            if record.img_url_vex:
                image = base64.b64encode(requests.get(record.img_url_vex.strip()).content).replace(b'\n', b'')
            record.write({'image_1920': image })
    '''


class Image(models.Model):
    _inherit        = 'product.image'
    id_vex          = fields.Char(string="Connector  ID")
    server_vex      = fields.Many2one('vex.instance')
    conector        = fields.Selection([])
    _sql_constraints = [
        ('unique_id_img_vex', 'unique(id_vex, conector, server_vex)',
         'There can be no duplication of synchronized Pictures ')
    ]
