from odoo import api, fields, models
import threading
import requests
import base64
from odoo.addons.payment.models.payment_acquirer import ValidationError
from datetime import datetime
from urllib.parse import urlparse
import logging
import pprint
import math
import html2text
from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)
from difflib import SequenceMatcher
from datetime import timedelta

id_api = "id_vex"
server_api = "server_vex"

class WooSynchro(models.TransientModel):
    _name = "vex.synchro"
    _description = "Synchronized server Vex"
    # server             = fields.Many2one('woo.synchro.server', "Server ", required=True)
    accion = fields.Many2one('vex.restapi.list', required=True)
    current_pag = fields.Integer()
    total_paginaciones = fields.Integer()
    argument = fields.Char(related="accion.argument")
    import_unit = fields.Boolean()
    id_vex = fields.Char(string='Id Connector')
    server_vex = fields.Many2one('vex.instance','Instance')
    conector   = fields.Char()

    @api.model
    def start_sync_automatic(self):
        #buscar el modelo del cron automatico
        cron = self.env['ir.cron'].search([('argument','=','vex_cron')],limit=1)
        #raise ValidationError(cron)
        if cron:
            if cron.server_vex and cron.accion:
                #raise ValidationError('ohh')
                self.synchronize(cron.accion, cron.server_vex, None)


    def get_total_data_count(self):
        return 0

    def get_total_count(self):
        return 0

    def import_all(self, server, accion):
        return 0

    def import_by_parts(self, server, query):
        return 0

    def get_data_id(self,id_vex,server,query):
        return 0

    def synchro_unit_wizard(self):
        self.synchro_unit(self.accion, self.accion.model ,self.server_vex, self.id_vex)

    def synchro_unit(self, accion, model , server_vex, id_vex, api=None):
        item = self.get_data_id(id_vex, server_vex,accion.argument)
        #raise ValidationError(accion.name)
        self.synchro(item, accion.argument, server_vex, model, accion, id_vex, None)

    def json_execute_create(self,table,data):
        table = str(table).replace('.', '_')
        filas_create = ''
        values_create= ''
        if table == 'product_template':
            data['active'] = "'t'"
            data['uom_id'] = 1
            data['uom_po_id'] = 1
            data['tracking'] = "'none'"
            data['sale_line_warn'] = "'no-message'"
            data['invoice_policy'] = "'order'"
            data['sale_ok'] = "'t'"
            data['purchase_ok'] = "'t'"
        for d in data:
            filas_create = filas_create + ', ' + str(d)
            values_create = values_create + ', ' + str(data[d])
        filas_create = filas_create[1:]
        values_create = values_create[1:]
        create = "INSERT INTO  {tabla} ({filas}) VALUES ({values}) ;".format(tabla=table,
                                                                           filas=filas_create,
                                                                           values=values_create)
        #if table == "vex_logs":
        #    raise ValidationError(create)
        self.env.cr.execute(create)

    def json_execute_update(self,table,data,id_vex):
        table = str(table).replace('.', '_')
        set_update = ''
        for d in data:
            set_update = set_update + ', ' + str(d) + '=' + str(data[d])
            set_update = set_update[1:]
        write = "UPDATE {tabla} set {set} where id = {id_vex} ;".format(tabla=table, set=set_update, id_vex=id_vex)
        #½raise ValidationError(write)
        self.env.cr.execute(write)

    def sql_fields(self, table, data,id_vex,api):
        #table = accion.model
        table = str(table).replace('.', '_')
        filas_create = ''
        values_create = ''
        set_update = ''
        if 'create' in data:
            #campos obligatorios
            #self.json_execute_create(table,data['create'])

            if table == 'product_template':
                data['create']['active'] = "'t'"
                data['create']['uom_id'] = 1
                data['create']['uom_po_id'] = 1
                data['create']['tracking'] = "'none'"
                data['create']['sale_line_warn'] = "'no-message'"
                data['create']['invoice_policy'] = "'order'"
                data['create']['sale_ok'] = "'t'"
                data['create']['purchase_ok'] = "'t'"
            for d in data['create']:
                filas_create = filas_create + ', ' + str(d)
                values_create = values_create + ', ' + str(data['create'][d])
            filas_create = filas_create[1:]
            values_create = values_create[1:]

        if 'write' in data:

            if table == 'product_template':
                data['write']['active'] = "'t'"
                data['write']['uom_id'] = 1
                data['write']['uom_po_id'] = 1
                data['write']['tracking'] = "'none'"
                data['write']['sale_line_warn'] = "'no-message'"
                data['write']['invoice_policy'] = "'order'"
                data['write']['sale_ok'] = "'t'"
                data['write']['purchase_ok'] = "'t'"
            for d in data['write']:
                set_update = set_update + ', ' + str(d) + ' = ' + str(data['create'][d])
            set_update = set_update[1:]

        create = "INSERT INTO  {tabla} ({filas}) VALUES ({values}) ON CONFLICT DO NOTHING".format(tabla=table,
                                                                           filas=filas_create,
                                                                           values=values_create)

        write = "UPDATE {tabla} SET {set} WHERE id_vex = '{id_vex}'".format(tabla=table, set=set_update, id_vex=id_vex)

        return {
            'create': create,
            'write': write,

        }
    def json_fields(self,data,query,server):
        return 0
    def import_stock(self,server,products):
        if not server.location_id:
            raise ValidationError('Set Up Location')
        location = server.location_id
        json_stock = {
            'name': 'INV Meli',
            'prefill_counted_quantity': 'counted',
            'location_ids': [(6, 0, [location.id])],
            'stock_vex': True
        }
        inventory = self.env['stock.inventory'].create(json_stock)
        json_variante = []
        for p in products:
            id_vex = p.id_vex
            variantes = self.env['product.product'].search([('product_tmpl_id', '=', p.id)])

            for variante in variantes:
                if variante.id_vex_varition:
                    query_pro_pro = "INSERT INTO product_product_stock_inventory_rel (stock_inventory_id,product_product_id) " \
                                    "VALUES " \
                                    "({},{})".format(inventory.id, variante.id)

                    #self.env.cr.execute(query_pro_pro)
                json_variante.append(variante.id)
        inventory.product_ids = [(6, 0, json_variante)]



        inventory.action_start()
        for p in products:
            variantes = self.env['product.product'].search([('product_tmpl_id', '=', p.id)])
            for variante in variantes:
                self.insert_lines_stock(id_vex, variante, inventory)
        inventory.action_validate()

    def insert_lines_stock(self, l, variante, inventory):
        invline = self.env['stock.inventory.line'].search(
            [('product_id', '=', int(variante.id)), ('inventory_id', '=', int(inventory.id))])
        if not invline:
            self.env['stock.inventory.line'].create({
                'product_id': variante.id,
                'product_qty': variante.stock_vex,
                'location_id': inventory.location_ids[0].id,
                'inventory_id': inventory.id,
                'product_uom_id': variante.uom_id.id,
                'company_id': inventory.company_id.id,
            })
        else:
            invline.write({
                'product_qty': variante.stock_vex
            })

        return 0
    def synchro_ext(self, data, query, server, table, accion,id_vex ,api,exist):
        return 0

    def synchro_threading(self,data,query,server,table,accion,id_vex,api):
        th = []

        for dr in data:
            threaded_synchronization = threading.Thread(target=self.except_synchro(dr, query, server, table, accion, id_vex, api))
            #threaded_synchronization = threading.Thread(self.except_synchro(m, accion, wcapi, server, table, fast))
            th.append(threaded_synchronization)
        for t in th:
            t.run()

        return 0

    def except_synchro(self, data, query, server, table, accion,id_vex ,api=None):
        self.synchro(data, query, server, table, accion, id_vex, api)
        '''
        try:
            self.synchro(data, query, server, table, accion,id_vex ,api)

        except:
            start_date = fields.Datetime.now()
            dx = {
                'start_date': "'{}'".format(start_date),
                'end_date': "'{}'".format(start_date),
                'description': "'Error importing {}  id {} : '".format(accion.name,data['body']['id'] if 'body' in data else data['id']),
                'state': "'error'",
                'server_vex': server.id,
                'vex_list': accion.id,
                #'conector': "{}".accion.conector
            }
            self.json_execute_create('vex.logs',dx)
        '''

    @api.model
    def synchro(self, data, query, server, table, accion,id_vex ,api=None):
        #raise ValidationError('kaa')
        conector = server.conector

        data_json = self.json_fields(data,query,server)
        #raise ValidationError(id_vex)
        sql_fields = self.sql_fields(table,data_json,id_vex ,api)
        #import json
        #raise ValidationError(json.dumps(sql_fields))
        if query == "products":
            exist = self.env[table].search([('id_vex', '=', str(id_vex)),
                                        ('conector', '=', conector),
                                        ('server_vex', '=', int(server.id)),
                                        '|',
                                        ('active', '=', True), ('active','=',False)])
        else:
            exist = self.env[table].search([('id_vex', '=', str(id_vex)),
                                            ('conector', '=', conector),
                                            ('server_vex', '=', int(server.id))])


        if not exist:
            self.env.cr.execute(sql_fields['create'])
        else:
            #raise ValidationError(sql_fields['write'])
            self.env.cr.execute(sql_fields['write'])
            #raise ValidationError('escribir')

        exist = self.env[table].search([('id_vex', '=', str(id_vex)),
                                        ('conector', '=', conector),
                                        ('server_vex', '=', int(server.id))])
        self.synchro_ext( data, query, server, table, accion,id_vex ,api,exist)
        return 0

    def synchronize(self, accion, server, wcapi):
        #raise ValidationError('holaa')
        table = str(accion.model)
        query = str(accion.argument)
        rango = int(accion.per_page)
        pag = self.get_pages(server, accion)
        current_page = 0
        ####
        total_data_count = 0
        total_pag = 0
        start_date = fields.Datetime.now()
        if accion.import_by_parts:
            raise ValidationError('por partes')
            self.import_by_parts()
            total_data_count = self.get_total_data_count()
            total_pag = math.ceil(total_data_count / rango)

            current_page = int(pag['current']) + 1
            self.import_by_parts(server, accion)
        else:
            #raise ValidationError('Total')
            tt = self.get_total_count()
            #raise ValidationError(tt)
            total_pag = tt
            current_page = tt
            self.import_all(server, accion)

        end_date = fields.Datetime.now()
        dx = {
            'start_date': "'{}'".format(start_date),
            'end_date': "'{}'".format(end_date),
            'description': "'{}  successfully synchro   '".format(accion.name),
            'state': "'done'",
            'server_vex': server.id,
            'vex_list': accion.id,
            # 'conector': "{}".accion.conector
        }
        self.json_execute_create('vex.logs', dx)
        #raise ValidationError('hols')


        if int(pag['current']) >= total_pag:
            return {
                'current': 0,
                'total': 0
            }


        #
        #

        return {
            'current': current_page,
            'total': total_pag
        }

    def get_pages(self, server, accionx):
        accion = self.env['vex.logs'].search([('server_vex', '=', server.id),
                                              ('state', '=', 'done'), ('stock', '=', False), ('webhook', '=', False),
                                              ('vex_list', '=', accionx.id)],
                                             order="id desc", limit=1)
        if accion:
            if int(accion.page) >= int(accion.total):
                tt = 0
            else:
                tt = int(accion.page)
        else:
            tt = 0
        return {
            'current': tt,
            'total': int(accion.total)
        }

    def check_synchronize(self, server):
        return 0

    def start_import(self):
        return 0
    def vex_import(self,  id_action, wcapi = None):
        server = self.server_vex
        #vex = self.vex_upload_download(server, wcapi)
        self.check_synchronize(server)
        accion = self.accion
        page = self.synchronize(accion, server, wcapi)
        #pag = self.get_pages(server, self.accion)
        pag = {'current':0}
        if int(pag['current']) == 0:
            view_rec = self.env.ref('base_conector_vex.vex_import_synchro_finish',
                                    raise_if_not_found=False)
        else:
            view_rec = self.env.ref('base_conector_vex.vex_import_synchro_finish_cron',
                                    raise_if_not_found=False)
        action = self.env.ref(
            id_action, raise_if_not_found=False
        ).read([])[0]
        action['views'] = [(view_rec and view_rec.id or False, 'form')]
        # action['target'] = 'new'
        return action

    def check_customer(self, dt, server , customer_id ,accion):
        data = {}
        #raise ValidationError(str(dt))
        data['customer'] = dt['customer']
        data['customer']['id_vex'] = "'{}'".format(customer_id)
        data['customer']['server_vex'] = server.id
        data['customer']['conector'] = "'{}'".format(server.conector)
        data['customer']['active'] = "'t'"
        billing, shipping , partner = None, None , None
        if customer_id != 0 or customer_id != None:
            # buscar la data del cliente en woocomerce
            #pr = wcapi.get("customers/" + str(customer_id)).json()
            # buscar el cliente en res.partner odoo
            partner = self.env['res.partner'].search([('id_vex', '=', str(customer_id)), ('server_vex', '=', int(server.id))])
            if not partner:

                self.json_execute_create('res.partner',data['customer'])
                partner = self.env['res.partner'].search([('id_vex', '=', str(customer_id)), ('server_vex', '=', int(server.id))])

                if 'billing' in data:
                    bi = data['billing']
                    bi['parent_id'] = partner.id
                    bi['type'] = 'invoice'
                    bi['id_vex_parent'] = partner.id_woo
                    #jsonc = self.json_fields(bi, 'customers', wcapi, server)
                    # query_customer = "INSERT INTO res_partner ()"
                    # billing = self.env['res.partner'].create(jsonc['create'])
                    billing = self.json_execute_create(bi)

                if 'shipping' in data:
                    # crear para envio envio
                    sh = data['shipping']
                    sh['parent_id'] = partner.id
                    sh['type'] = 'delivery'
                    sh['id_vex_parent'] = partner.id_woo
                    #jsons = self.json_fields(sh, 'customers', wcapi, server)
                    #self.env.cr.execute(jsons['create'])
                    shipping = self.json_execute_create(sh)

            '''
            # buscar el cliente de facturacion en odoo
            billing = self.env['res.partner'].search([('parent_id', '=', partner.id), ('type', '=', 'invoice')],limit=1)
            if not billing:
                bi = data['billing']
                bi['parent_id'] = partner.id
                bi['type'] = 'invoice'
                bi['id_vex_parent'] = partner.id_vex
                billing = self.json_execute_create(bi)
                #jsonc = self.json_fields(bi, 'customers', wcapi, server)
                #billing = self.env['res.partner'].create(jsonc['create'])
            shipping = self.env['res.partner'].search([('parent_id', '=', partner.id), ('type', '=', 'delivery')])
            if not shipping:
                sh = data['shipping']
                sh['parent_id'] = partner.id
                sh['type'] = 'delivery'
                sh['id_woo_parent'] = partner.id_woo
                jsons = self.json_fields(sh, 'customers', wcapi, server)
                shipping = self.env['res.partner'].create(jsons['create'])
            # raise ValidationError(partner.id)
            '''

        else:
            partner = self.json_execute_create('res.partner',data['customer'])
            '''
            # datos para la facturacion
            billing = data['billing']
            # datos para el envio
            shipping = data['shipping']
            # country = self.get_country(billing['country'])
            # state   = self.get_state(country ,billing['state'])
            partner = self.env['res.partner'].create({
                'name': str(data['billing']['first_name']) + " " + str(data['billing']['last_name']),
                'woo_first_name': str(data['billing']['first_name']),
                'woo_last_name': str(data['billing']['last_name']),
                'phone': str(data['billing']['phone']),
                'email': data['billing']['email'],
                'property_product_pricelist': server.pricelist.id,
                'server': server.id,
                'orden_woo_id': data['id']
            })

            bi = data['billing']
            bi['parent_id'] = partner.id
            bi['type'] = 'invoice'
            bi['id_woo_parent'] = partner.id_woo
            jsonc = self.json_fields(bi, 'customers', wcapi, server)
            billing = self.env['res.partner'].create(jsonc['create'])

            sh = data['shipping']
            sh['parent_id'] = partner.id
            sh['type'] = 'delivery'
            sh['id_woo_parent'] = partner.id_woo
            jsons = self.json_fields(sh, 'customers', wcapi, server)
            shipping = self.env['res.partner'].create(jsons['create'])
            '''


        return {
            'customer': partner,
            'invoice': billing if billing else partner,
            'shipping': shipping if shipping else partner
        }

    def insert_fee_lines(self, fee_lines, creado, server,key,key_total,sg):
        total_fee = 0
        if fee_lines:
            for f in fee_lines:
                iw = f[key]
                total_fee += float(f[key_total]*sg)
                ppf = self.env['product.template'].search([('server_vex', '=', server.id), ('id_vex', '=', iw)])
                if not ppf:
                    crea = {
                        'name':  "'fee_"+str(iw)+"'",
                        'id_vex': "'"+str(iw)+"'",
                        'list_price': float(f[key_total]*sg),
                        'server_vex': server.id,
                        'type':"'service'",
                        'conector': "'"+str(server.conector)+"'",
                        'categ_id': server.categ_id.id,

                    }
                    self.json_execute_create('product.template',crea)
                ppf = self.env['product.template'].search([('server_vex', '=', server.id), ('id_vex', '=', iw)])
                #raise ValidationError(ppf)
                pp = self.env['product.product'].search([('server_vex', '=', server.id), ('product_tmpl_id', '=', ppf.id)])
                if not pp:
                    crea = {
                        'product_tmpl_id': ppf.id,
                        'active': "'t'"
                    }
                    self.json_execute_create('product.product',crea)
                pp = self.env['product.product'].search([('product_tmpl_id', '=', ppf.id)],limit=1)
                #raise ValidationError(pp)

                new_line = {
                    # 'name':str(existe.name),
                    'name': "'" + str(pp.name) + "'",
                    'product_id': pp.id,
                    'product_uom_qty': 1,
                    'price_unit': float(f[key_total]*sg),
                    'price_reduce': float(f[key_total]*sg),
                    'price_reduce_taxinc': float(f[key_total]*sg),
                    'price_reduce_taxexcl': float(f[key_total]*sg),
                    'order_id': creado.id,
                    'price_subtotal': float(f[key_total]*sg),
                    'price_total': float(f[key_total]*sg),
                    'price_tax': 0.0,
                    # campos requeridos
                    'customer_lead': 1.0,
                    'invoice_status': "'no'",
                    'company_id': server.company.id,
                    'currency_id': creado.currency_id.id,
                    'product_uom': 1,
                    'discount': 0

                }

                self.json_execute_create('sale.order.line', new_line)
        return total_fee

    def insert_lines(self,lines,server,creado , accion):

        for p in lines:
            #raise ValidationError(p['quantity'])
            existe = self.check_product_order(p['item'] ,server , accion)

            p_id = existe.id
            if not p_id:
                #no se encontro elproducto por alguna razon
                #crear producto temporal
                temp = self.env['product.product'].search([('id_vex_varition','=','tmp')])
                if not temp:
                    temp = self.env['product.product'].create({
                        'name':'Producto temporal conector',
                        'id_vex_varition': 'tmp'
                    })
                p_id = temp.id

                start_date = fields.Datetime.now()
                dx = {
                    'start_date': "'{}'".format(start_date),
                    'end_date': "'{}'".format(start_date),
                    'description': "'Error importing {}  product id {} : '".format(accion.name, p['item']['id']),
                    'state': "'error'",
                    'server_vex': server.id,
                    'vex_list': accion.id,
                    'detail': "'Error importing {}  product id {} in order id {} '".format(accion.name, p['item']['id'],creado.id_vex),
                }

                self.json_execute_create('vex.logs', dx)



            #raise ValidationError(existe)
            new_line = {
                                    #'name':str(existe.name),
                                    'name': "'"+str(existe.name)+"'",
                                    'product_id': p_id,
                                    'product_uom_qty': int(p['quantity']),
                                    'price_unit': float(p['unit_price']),
                                    'price_reduce': float(p['unit_price']),
                                    'price_reduce_taxinc': float(p['unit_price']),
                                    'price_reduce_taxexcl': float(p['unit_price']),
                                    'order_id': creado.id,
                                    'price_subtotal': float(p['unit_price']) * int(p['quantity']),
                                    'price_total': float(p['unit_price']) * int(p['quantity']),
                                    'price_tax': 0.0,
                                    #campos requeridos
                                    'customer_lead':1.0,
                                    'invoice_status':"'no'",
                                    'company_id': server.company.id,
                                    'currency_id': creado.currency_id.id,
                                    'product_uom': 1,
                                    'discount':0

                                }

            try:
                self.json_execute_create('sale.order.line',new_line)
            except:
                start_date = fields.Datetime.now()
                dx = {
                    'start_date': "'{}'".format(start_date),
                    'end_date': "'{}'".format(start_date),
                    'description': "'Error creating line order  {}  product id {} : '".format(accion.name, p['item']['id']),
                    'state': "'error'",
                    'server_vex': server.id,
                    'vex_list': accion.id,
                    'detail': "'Error creating {}  product id {} in order id {} '".format(accion.name, p['item']['id'],
                                                                                           p['id']),
                }

                self.json_execute_create('vex.logs', dx)

    def check_product_order(self,p  , server , accion):
        #raise ValidationError(str(p))
        pp = None
        atributo = p['variation_id']
        #condicion para verificar si es un atributo
        if  atributo:
            #raise ValidationError(atributo)
            #buscar en product product
            pp = self.env['product.product'].search([('id_vex_varition','=',int(atributo)),('server_vex','=',int(server.id)),])
            #si no existe crearlo
            if not pp:
                self.check_produc(p['id'], server ,accion)
                pp = self.env['product.product'].search([('id_vex_varition', '=', int(atributo)),('server_vex', '=', int(server.id))])
        else:
            pt = self.check_produc(p['id'],  server , accion)
            #raise ValidationError(pt.id_vex)
            #raise ValidationError(pt.product_variant_ids)

            pp = self.env['product.product'].search([('product_tmpl_id', '=', int(pt.id))])
            #raise ValidationError(pp)
        return  pp

    def check_produc(self,id ,server,accion):
        pro_id = None
        existe = self.env['product.template'].search([(id_api, '=', str(id)),(server_api,'=',int(server.id))])
        #raise ValidationError(existe)
        if existe:
            pro_id = existe
        else:
            self.synchro_unit(accion,'product.template',server,id)
            #raise ValidationError('no existe')
            pro_id = self.env['product.template'].search([(id_api, '=', str(id)),(server_api,'=',int(server.id))])
        return  pro_id

    '''
    def check_product_order(self, p, wcapi, server, orden):
        # raise ValidationError(p)
        pp = None
        # verificar si es un atributo
        atributo = int(p['variation_id'])

        if atributo > 0:
            # buscar en product product
            pp = self.env['product.product'].search([('id_vex_varition', '=', str(atributo)),
                                                     ('server_vex', '=', int(server.id))])
            if not pp:
                pt = self.check_produc(p['product_id'], wcapi, server)
                pp = self.env['product.product'].search([('id_vex_varition', '=', str(atributo)),
                                                         ('server_vex', '=', int(server.id))])
        else:
            # raise ValidationError(p['product_id'])
            if int(p['product_id']) == 0:
                iw = 'tmp_' + str(p['id']) + 'orden_' + str(orden['id'])
                pt = self.env['product.template'].search([('id_woo', '=', iw), ('server', '=', server.id)])
                if not pt:
                    pt = self.env['product.template'].create({
                        'name': p['name'],
                        'id_woo': iw,
                        'lst_price': p['total'],
                        'server': server.id
                    })
                pp = self.env['product.product'].search([('product_tmpl_id', '=', pt.id)])
                # raise ValidationError(pp)

                return pp
            else:
                pt = self.check_produc(p['product_id'], wcapi, server)
                pp = self.env['product.product'].search([('product_tmpl_id', '=', pt.id)])
                if not pp:
                    query = "INSERT INTO product_product (product_tmpl_id,woo_regular_price,active)  VALUES" \
                            "({},{},'t')".format(pt.id, pt.list_price)
                    # raise  ValidationError(query)
                    self.env.cr.execute(query)
                pp = self.env['product.product'].search([('product_tmpl_id', '=', pt.id)])
                count = self.env['product.product'].search_count([('product_tmpl_id', '=', pt.id)])
                if count > 0:
                    pp = pp[0]

        return pp
    '''
