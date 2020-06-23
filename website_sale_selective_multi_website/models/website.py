# -*- coding: utf-8 -*-
# LGPL-3
from odoo import api, models


class Website(models.Model):
    _inherit = "website"

    def sale_product_domain(self):
        super(Website, self).sale_product_domain()
        domain = [
            ("sale_ok", "=", True),
            '|',
            ('website_ids', 'in', (self.id)),
            ('website_ids', '=', False)]
        return domain
