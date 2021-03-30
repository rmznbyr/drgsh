import requests
import threading
import base64
from ..models.vex_soluciones_meli_config  import API_URL, INFO_URL, get_token
from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
from ..models.vex_soluciones_meli_config  import API_URL, INFO_URL, get_token
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

id_api       = 'id_vex'
server_api   = 'server_vex'

class MeliActionSynchro(models.TransientModel):
    _inherit       = "vex.synchro"
    def get_data_id(self,id_vex,server,query):
        res = super(MeliActionSynchro, self).get_data_id(id_vex,server,query)
        if server.conector == 'meli':
            #raise ValidationError('h')
            if query == "products":
                item_url = '{}/items?ids={}&access_token={}'.format(API_URL, id_vex, server.access_token)
                #raise ValidationError(item_url)
                item = requests.get(item_url).json()
                return item[0]
            if query == "orders":
                #item_url = '{}/orders/{}&access_token={}'.format(API_URL, id_vex, server.access_token)
                url = 'https://api.mercadolibre.com/orders/{}'.format(id_vex)
                headers = {
                    "Accept": "application/json",
                    "Authorization": "Bearer " + str(server.access_token)
                }
                res = requests.get(url, headers=headers).json()
                return res
                #raise ValidationError(str(res))
            #raise ValidationError(str(item))

        return res

    def insert_import_lines(self, server,accion,products_url,res):
        lines_wait = self.env['vexlines.import'].search([('accion', '=', accion.id),
                                                         ('instance','=',server.id)], limit=1)
        #raise ValidationError(lines_wait)
        if not lines_wait:
            #EJEUTA LA PRIMERA VES
            last = 0
            arg = ",".join(res['results'])


            self.json_execute_create('vexlines.import', {
                'url':  "'"+str(arg)+"'",
                'orden': last,
                'instance': server.id,
                'state': "'done'",
                'accion':accion.id
            })
            scroll_id = res['scroll_id']

            products_url = '{}/users/{}/items/search?search_type=scan&scroll_id={}&access_token={}'.format(API_URL,
                                                                                              str(server.user_id),scroll_id,
                                                                                              str(server.access_token))
            #raise ValidationError(products_url)
            res = requests.get(products_url).json()
            #import json
            #raise ValidationError(json.dumps(res))
            if res['results']:
                self.insert_import_lines(server,accion,products_url,res)

        else:
            last = self.env['vexlines.import'].search([('accion', '=', accion.id), ('instance', '=', server.id),
                                                       ('state', '=', 'done')], limit=1)
            last = int(last.orden) + 1
            arg = ",".join(res['results'])
            self.json_execute_create('vexlines.import', {
                'url': "'" + str(arg) + "'",
                'orden': last,
                'instance': server.id,
                'state': "'wait'",
                'accion': accion.id
            })
            scroll_id = res['scroll_id']
            products_url = '{}/users/{}/items/search?search_type=scan&scroll_id={}&access_token={}'.format(API_URL,
                                                                                                           str(server.user_id),
                                                                                                           scroll_id,
                                                                                                           str(server.access_token))
            res = requests.get(products_url).json()
            if res['results']:
                self.insert_import_lines(server,accion,products_url,res)
            else:
                #activar el cron
                update_cron = "UPDATE ir_cron SET accion={} , server_vex={}  WHERE argument = 'vex_cron' ".format(accion.id,server.id)
                self.env.cr.execute(update_cron)
                cron = self.env['ir.cron'].search([('argument', '=','vex_cron' ),("active", "=", False)])
                if cron:
                    cron.active = True
        return 0
    @api.model
    def meli_api(self, server, query, accion,filtro):

        if query == "products":
            lines_wait = self.env['vexlines.import'].search([('accion', '=', accion.id),
                                                             ('instance', '=', server.id),
                                                             ('instance', '=', server.id), ('state', '=', 'wait')],
                                                            limit=1)
            #raise ValidationError(lines_wait)
            if not lines_wait:
                self.env['vexlines.import'].search([('accion', '=', accion.id),('instance', '=', server.id)]).unlink()

            res = None
            array_products = []
            if lines_wait:
                #raise ValidationError(lines_wait)
                item_str = lines_wait.url

                res = item_str.split(',')
                #raise ValidationError(res)

                lines_wait.state = 'done'

            else:
                products_url = '{}/users/{}/items/search?search_type=scan&access_token={}'.format(API_URL,
                                                                                              str(server.user_id),
                                                                                              str(server.access_token))
                #raise ValidationError(products_url)
                res = requests.get(products_url).json()
                self.insert_import_lines(server,accion,products_url,res)
                res = res[filtro]

            for r in res:
                #raise ValidationError(str(r))
                item = self.get_data_id(r, server,query)
                array_products.append(item)


            # string_items = ','.join(res)
            # item_url = '{}/items?ids={}&access_token={}'.format(API_URL,string_items,server.access_token)
            # raise ValidationError(item_url)
            # items = requests.get(item_url).json()
            # raise ValidationError(products_url)

            return array_products
        if query == 'categories':
            categories_url = "https://api.mercadolibre.com/sites/{}/categories".format(server.meli_country)
            res = requests.get(categories_url).json()
            return res
        if query == "orders":
            orders_url = '{}/orders/search?seller={}&access_token={}'.format(API_URL, str(server.user_id),
                                                                             str(server.access_token))
            #raise ValidationError(orders_url)
            res = requests.get(orders_url)
            res = res.json()[filtro]
            return res


    def get_total_data_count(self):
        res = super(MeliActionSynchro, self).get_total_data_count()
        return res

    def import_by_parts(self,server,query):
        res = super(MeliActionSynchro, self).import_by_parts(server,query)
        if server.conector == 'meli':
            data_request = self.meli_api(server, query, 'results')
            import json
            raise ValidationError(json.dumps(data_request))


        return res

    def get_total_count(self):
        res = super(MeliActionSynchro, self).get_total_count()
        return res

    def json_fields(self,data,query,server,accion=None):
        res = super(MeliActionSynchro, self).json_fields(data,query,server)
        if server.conector == 'meli':
            create = {}
            write = {}
            if query == "products":
                if not 'body' in data:
                    import json
                    raise ValidationError('ka')
                    #raise ValidationError('no existe body in data')
                body = data['body']
                #raise ValidationError(str(body))

                create = {
                    'conector': "'meli'",
                    'server_vex': server.id,
                    'id_vex': "'"+body['id']+"'",
                    'name': "'"+body['title']+"'",
                    'list_price': body['price'],
                    'type': "'product'",
                    'categ_id': server.categ_id.id,
                    #'image_1920': base64.b64encode(myimage.content),
                    #'is_published': active,
                    #'product_condition': body['condition'],
                    #'active_meli': active,
                    'permalink': "'{}'".format(body['permalink']),
                    #'public_categ_ids': [(6, 0, [self.check_categories(body['category_id'], server, None).id])]
                }
                write = {
                    'name': "'" + body['title'] + "'",
                    'list_price': body['price'],
                    'type': "'product'",
                    'categ_id': server.categ_id.id,
                    'permalink': body['permalink'],
                }

            if query == "orders":
                d = str(data['date_created']).split('.')
                #raise ValidationError(d[0])
                fecha = datetime.strptime(d[0], '%Y-%m-%dT%H:%M:%S')
                pricelist = server.pricelist
                if not pricelist:
                    raise ValidationError("Set Up pricelist")
                salesteam = server.sales_team
                if not salesteam:
                    raise ValidationError("Set Up Sales Team")
                if not server.warehouse:
                    raise ValidationError("Set Up Warehouse")
                dx = {'customer':{}}
                nam = "'{}'".format(str(data['buyer']['first_name'])+" "+str(data['buyer']['last_name']))
                dx['customer']['name'] , dx['customer']['display_name'] = nam , nam
                if 'phone' in dx['customer']:
                    dx['customer']['phone'] = "'{}'".format(str(data['buyer']['phone']['area_code'])+"-"+str(data['buyer']['phone']['number']))

                customer = self.check_customer(dx, server , data['buyer']['id'] ,accion)
                sqx = server.sequence_id
                if not sqx:
                    raise ValidationError('sequence not found in instance')
                seq = self.env['ir.sequence'].next_by_code(sqx.code)
                state = self.env['vex.instance.status.orders'].search([('instance','=',server.id),('value','=',data['status'])])

                if state:
                    state =state.odoo_state
                else:
                    state = 'draft'
                #raise ValidationError(state)
                create = {

                    'conector': "'meli'",
                    'server_vex': server.id,
                    'id_vex': "'" + str(data['id']) + "'",
                    'name': "'" + str(seq) + "'",
                    'partner_id': customer['customer'].id,
                    'partner_invoice_id': customer['invoice'].id,
                    'partner_shipping_id': customer['shipping'].id,
                    'pricelist_id': server.pricelist.id,
                    'date_order': "'"+str(fecha)+"'",
                    'amount_untaxed': float(data['total_amount']),
                    'amount_total': float(data['total_amount']),
                    #'woo_status': "'"+str(['status']) + "'",
                    #'woo_customer_ip_address': "'"+str(data['customer_ip_address']) + "'",
                    'team_id': salesteam.id,
                    #'woo_date_created': "'"+str(data['date_created']) + "'",
                    #'woo_payment_method': "'"+str(data['payment_method_title']) + "'",
                    'payment_term_id': server.payment_term.id,
                    'picking_policy': "'" + str(server.picking_policy) + "'",
                    'warehouse_id': server.warehouse.id,
                    'state': "'{}'".format(state),
                    'company_id' : server.company.id
                }
                write = {
                    'state': "''".format(state),
                }

            return {
                'create': create,
                'write': write,
            }
        return res

    def import_all(self,server,accion):
        res = super(MeliActionSynchro, self).import_all(server,accion)
        if server.conector == 'meli':
            query = str(accion.argument)
            #raise ValidationError('whatt')
            data_request = self.meli_api(server, query,accion ,'results')
            #raise ValidationError(str(data_request))
            #self.synchro_threading(data_request,query, server, str(accion.model), accion, None , api)
            # importar stock
            if accion.argument == 'products':
                products = []
                ids_vex = []
                data = data_request
                #raise ValidationError(len(data))

                #data = data
                #raise ValidationError(len(data))
                for d in data:
                    #raise ValidationError(str(d))
                    id_vex = d['body']['id']
                    pro = self.env['product.template'].search([('id_vex','=',str(id_vex))])
                    products.append(pro)
                #raise ValidationError(ids_vex)
                self.import_stock(server,products)
        return res

    def synchro(self, data, query, server, table, accion,id_vex ,api):

        if server.conector == 'meli':
            if query == "products":
                #raise ValidationError(str(data))
                try:
                    data = data[0]
                except:
                    data = data
            #if query == "products" and server.import_products_paused == False:
            #    if dr['body']['status'] != 'active':
            #       continue

            #raise ValidationError(str(data))
            id_vex = data['body']['id'] if query == "products" else data['id']
        res = super(MeliActionSynchro, self).synchro(data, query, server, table, accion, id_vex, api)
        return res

    def synchro_ext(self,dr, query, server, table, accion, id_vex , api ,exist):
        #raise ValidationError(exist)
        res = super(MeliActionSynchro, self).synchro_ext(dr, query, server, table, accion, id_vex , api ,exist )
        if server.conector == 'meli':
            if query == "products":
                self.insert_variations(dr['body'], server, exist)
                '''
                self.check_imagenes(dr['body']['pictures'], server, exist)
                #insertar la imagen del producto
                
                '''
                url = dr['body']['thumbnail']
                exist.write({
                    'image_1920': base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b''),
                })
            if query == 'orders':
                self.insert_lines(dr['order_items'],server,exist, accion)
                if server.discount_fee:
                    total_fee = self.insert_fee_lines(dr['order_items'],exist,server,'listing_type_id','sale_fee',-1)
                    tt = exist.amount_total + float(total_fee)
                    self.json_execute_update('sale.order', {
                        'amount_untaxed': tt,
                        'amount_total': tt
                    }, exist.id)


        return res





