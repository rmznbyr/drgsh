from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
class VexRestapilist(models.Model):
    _name                = "vex.restapi.list"
    _description         = "List Vex RestApi"
    name                 = fields.Char(required=True)
    argument             = fields.Char()
    model                = fields.Char()
    log                  = fields.One2many('vex.logs','vex_list')
    interval             = fields.Integer(default=60)
    interval_type        = fields.Selection([('minutes', 'Minutes'),('hours', 'Hours'),
                                      ('days', 'Days'),('weeks', 'Weeks'),('months', 'Months')],default='minutes')
    active_cron          = fields.Boolean(default=False)
    interval_stock       = fields.Integer(default=60)
    interval_type_stock  = fields.Selection([('minutes', 'Minutes'), ('hours', 'Hours'),
                                      ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], default='minutes')
    active_cron_stock    = fields.Boolean(default=False)
    automatic            = fields.Boolean()
    ver                  = fields.Char(compute='_generate_ver')
    total_count          = fields.Integer(compute='_generate_count')
    next_date_cron       = fields.Datetime(compute='_generate_next_date',string="Next Execution Date")
    next_date_cron_stock = fields.Datetime(compute='_generate_next_date_stock', string="Next Execution Date")
    export               = fields.Boolean()
    importv              = fields.Boolean()
    per_page = fields.Integer(default=10, required=True,
                              string="Maximum number of items per page (min=1,max=100)")
    all_items = fields.Boolean(default=True)
    max_items = fields.Integer(string="Maximum number of items to be returned approximately")
    import_images = fields.Boolean()
    import_by_parts = fields.Boolean()
    conector             = fields.Selection([])

    _sql_constraints = [
        ('unique_id_argument', 'unique(argument,conector)', 'There can be no duplication of argument in conector')
    ]

    def go_action_products(self):
        return {
            'name': 'Products '+str(self.conector),
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'domain': "[('conector','=','{}')]".format(self.conector)
        }

    def stop_sync(self):
        cron = self.env['ir.cron'].search([('argument','=',str(self.argument)),('conector', '!=', False),
                                               ('automatic','=',True)])
        if cron:
            cron.active = False


    def _generate_next_date(self):
        cron = self.env['ir.cron'].search([('argument', '=', str(self.argument)),('conector', '!=', False),('automatic','=',False),
                                           "|",
                                           ("active", "=", True), ("active", "=", False)])
        if cron:
            self.next_date_cron = cron.nextcall
        else:
            self.next_date_cron = None
    def _generate_next_date_stock(self):
        cron = self.env['ir.cron'].search([('argument', '=', 'stock'),('conector', '!=', False),('automatic','=',False),
                                           "|",
                                           ("active", "=", True), ("active", "=", False)])
        if cron:
            self.next_date_cron_stock = cron.nextcall
        else:
            self.next_date_cron_stock = None

    #@api.model
    def _generate_count(self):
        for record in self:
            #buscar la cantidad
            model = record.model
            if model:
                count = self.env[str(model)].search_count([('conector', '=', str(record.conector)),('id_vex', '!=', False)])

                argument = record.argument
                if argument == 'products':
                    count = self.env[str(model)].search_count([('conector', '=', str(record.conector)),('id_vex', '!=', False),
                                                               ('type','=','product')])
                if argument == 'fee':
                    count = self.env[str(model)].search_count([('conector', '=', str(record.conector)),('id_vex', '!=', False),
                                                               ('type','=','service')])

                record.total_count = count

            else:
                record.total_count = 0