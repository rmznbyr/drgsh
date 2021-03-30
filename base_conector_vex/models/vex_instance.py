from odoo import api, fields, models
class VexInstance(models.Model):
    _name        = "vex.instance"
    _description = "Instance Vex"
    name = fields.Char(string='Server name', required=True)
    company = fields.Many2one('res.company',required=True)
    picking_policy = fields.Selection([('direct', 'Deliver each product when available'),
                                       ('one', 'Deliver all products at once')], default='direct')
    location_id = fields.Many2one('stock.location', string="Stock Location")
    journal_id = fields.Many2one('account.journal', required=True,
                                 domain="[('type','in',('bank','cash'))]")
    payment_term = fields.Many2one('account.payment.term')
    order_after = fields.Datetime()
    all_orders = fields.Boolean(defaul=True)
    all_status_orders = fields.Boolean(defaul=True, string='All the states')
    total_products = fields.Integer(compute='_generate_total')
    total_categories = fields.Integer(compute='_generate_total')
    total_customers = fields.Integer(compute='_generate_total')
    total_orders = fields.Integer(compute='_generate_total')
    conector = fields.Selection([])
    categ_id = fields.Many2one('product.category', string="product category", required=True)
    active_automatic = fields.Boolean(default=False, string="Activate automatic sync")
    warehouse = fields.Many2one('stock.warehouse', required=True)
    pricelist = fields.Many2one('product.pricelist')
    sales_team = fields.Many2one('crm.team', string="Sales Team")
    import_lines = fields.One2many('vexlines.import','instance')
    sequence_id = fields.Many2one('ir.sequence')
    state_orders = fields.One2many('vex.instance.status.orders','instance')
    discount_fee = fields.Boolean(defaul=False,required=True)
    import_stock = fields.Boolean(default=True)
    @api.model
    def default_get(self,fields):
        res = super(VexInstance,self).default_get(fields)
        sq = self.env['ir.sequence'].search([('code','=','sale.order')],limit=1)
        if sq:
            res.update({'sequence_id': sq.id})
        return res

    def _generate_total(self):
        for record in self:
            # buscar todos los productos para este servidor
            products = self.env['product.template'].search_count(
                [('id_vex', '!=', False), ('server_vex', '=', int(record.id))])
            record.total_products = products
            # categories = self.env['product.public.category'].search_count([(id_api, '!=', False), (server_api, '=', int(record.id))])
            record.total_categories = 0
            # customers = self.env['res.partner'].search_count([(id_api, '!=', False), (server_api, '=', int(record.id))])
            record.total_customers = 0
            # orders = self.env['sale.order'].search_count([(id_api, '!=', False), (server_api, '=', int(record.id))])
            record.total_orders = 0

    def fun_test(self):
        return 0

    def stop_sync(self):
        cron = self.env['ir.cron'].search([('argument', '=', 'vex_cron'),
                                           "|",
                                           ("active", "=", True), ("active", "=", False)])
        if cron:
            cron.active = False

    class VexImportLines(models.Model):
        _name = "vexlines.import"
        url   = fields.Char(required=True)
        orden = fields.Integer(required=True)
        instance = fields.Many2one('vex.instance',required=True)
        accion   = fields.Many2one('vex.restapi.list',required=True)
        state    = fields.Selection([('done','Realizado'),('wait','Pendiente')],default="wait")



