import requests
import threading

from ..models.vex_soluciones_meli_config  import API_URL, INFO_URL, get_token
#from ..models.vex_soluciones_product_template import Product
from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError



import logging
_logger = logging.getLogger(__name__)

id_api       = 'id_vex'
server_api   = 'server_meli'

class MeliActionSynchro(models.TransientModel):
    _name               = "meli.action.synchro"
    _description        = "Synchronized Server"
    server              = fields.Many2one('meli.synchro.instance',
                             "Instance", required=True)

    def check_synchronize(self,server):
        access_token = server.access_token
        res = requests.get(INFO_URL, params={'access_token': access_token})

        if res.status_code != 200:
            token = get_token(server.app_id, server.secret_key, server.redirect_uri, '', server.refresh_token)
            if token:
                update = {
                    'access_token' : token['access_token'],
                    'refresh_token' : token['refresh_token'],
                }
                #exist = self.env['meli.synchro.instance'].search([('user_id', '=', str(server.user_id))])
                server.write(update)


    @api.model
    def insert_variants(self, variants, pictures, product,server):
        product_product = self.env['product.product'].search([('product_tmpl_id', '=', int(product.id))])
        pictures_dict = dict()

        for picture in pictures:
            pictures_dict[picture['id']] = picture['url']

        for variant in variants:
            variant_id       = variant['id']
            variant_price    = variant['price']
            variant_image_id = variant['picture_ids'][0]
            variant_combinations = variant['attribute_combinations']
            variant_attr_ids = []
            for combination in variant_combinations:
                #buscar el atributo
                attribute = self.env['product.attribute'].search([('id_app', '=', str(combination['id'])),
                                                                  ('server_meli','=',server.id)])
                attr_value = combination['value_name']
                attr_line = self.env['product.attribute.value'].search([('name', '=', str(attr_value)), ('attribute_id', '=', attribute.id)])
                if not attr_line:
                    raise ValidationError(str(attribute.id)+'-'+str(combination['id'])+'/'+str(attr_value))

                variant_attr_ids.append(attr_line.id)
            #if str(variant_id) == '67216440550':
            #    raise ValidationError(variant_attr_ids)


            attr_value_ids = []
            for produc in product_product:
                for attr_value_id in produc.product_template_attribute_value_ids:
                    attr_value_ids.append(attr_value_id.product_attribute_value_id.id)

                bb = list(set(variant_attr_ids).intersection(attr_value_ids))


                if len(variant_attr_ids) == len(bb):
                    #if produc.id == 41:
                    #    raise ValidationError('sii')
                    #if set(variant_attr_ids) == set(attr_value_ids):
                    variant_image = requests.get(pictures_dict[variant_image_id])
                    produc.write({
                        'id_app_varition': str(variant_id),
                        'meli_regular_price': float(variant_price),
                        'image_1920' : base64.b64encode(variant_image.content),
                    })
                attr_value_ids = []

    @api.model
    def check_customer(self,dr,server):
        buyer_exist = self.env['res.partner'].search([(id_api, '=', str(dr['id'])), ('server_meli', '=', server.id)])
        if not buyer_exist:
            buyer_exist = self.env['res.partner'].create({
                        'name': str(dr['first_name']) + ' ' + str(dr['last_name']) ,
                        'id_app' : str(dr['id']),
                        'server_meli': server.id,
                        'email':str(dr['email']),
                        'phone':str(dr['phone']['area_code'])+str(dr['phone']['number'])
                    })
        return  buyer_exist

    #funcion donde se declaran los valores a importar
    @api.model
    def json_fields(self, dr, query,  server):
        # inicializando variables create y write
        create = {}
        write = {}

        if query == "products":
            body = dr['body']
            active = True if  body['status'] == 'active' else False

            thumbnail = body['thumbnail']
            myimage = requests.get(thumbnail)
            id_category = body['category_id']
            available_product = body['available_quantity']



            create = {
                            'server_meli'      : server.id,
                            'id_app'           : body['id'],
                            'name'             : body['title'],
                            'currency_id'      : body['currency_id'],
                            'list_price'       : body['price'],
                            'type'             : 'product',
                            'image_1920'       : base64.b64encode(myimage.content),
                            'is_published'     : active,
                            'product_condition': body['condition'],
                            'active_meli'           : active,
                            'permalink'        : body['permalink'],
                            'public_categ_ids' : [(6, 0, [self.check_categories(body['category_id'],server,None).id])]
                        }
            write = create
            if server.company:
                create['company_id']  = server.company.id
                write['company_id']   = server.company.id

        if query == "questions":
            create = {
                            'id_app' : dr['item_id'],
                            'server_meli': server.id,
                            'question_id' : dr['id'],
                            'date_created' : dr['date_created'],
                            'product_id' : dr['product_id'],
                            'seller_id' : dr['seller_id'],
                            'status' : dr['status'],
                            'text' : dr['status'],
                            'answer_text' : dr['answer']['text'] if dr['answer'] else '',
            }

            write = create

        if query == "categories":
            create = {
                'name':dr['name'],
                 'id_app' : dr['id'],
                 'server_meli': server.id,
                }

            write = create
        if query == "orders":
            create = {
                        'partner_id': self.check_customer(dr['buyer'],server).id,
                        'id_app' : dr['id'],
                        'server_meli': server.id,
                        'pricelist_id': server.pricelist.id,
                        #'meli_order_id' : meli_order_id,
                        #'meli_status' : meli_status,
                        #'meli_status_detail' : meli_status_detail,
                        #'meli_total_amount' : meli_total_amount,
                        'warehouse_id'            :   server.warehouse.id
                    }
            write = {
                'pricelist_id': server.pricelist.id,
                'warehouse_id'            :   server.warehouse.id
                }
            if server.company:
                create['company_id']  = server.company.id
                write['company_id']   = server.company.id


        result = {
            'create': create,
            'write': write,

        }
        return result

    @api.model
    def meli_api(self,server,query,filtro):
        if query == "products":
            products_url = '{}/users/{}/items/search?search_type=scan&access_token={}'.format(API_URL, str(server.user_id),str(server.access_token))
            res = requests.get(products_url)
            res = res.json()[filtro]
            array_products = []
            for r in res:
                item_url = '{}/items?ids={}&access_token={}'.format(API_URL,r,server.access_token)
                item = requests.get(item_url).json()
                array_products.append(item)

            #string_items = ','.join(res)
            #item_url = '{}/items?ids={}&access_token={}'.format(API_URL,string_items,server.access_token)
            #raise ValidationError(item_url)
            #items = requests.get(item_url).json()
            #raise ValidationError(products_url)
            return  array_products
        if query == 'categories':
            categories_url =  "https://api.mercadolibre.com/sites/{}/categories".format(server.meli_country)
            res = requests.get(categories_url).json()
            return  res
        if query == "orders":
            orders_url = '{}/orders/search?seller={}&access_token={}'.format(API_URL,str(server.user_id),str(server.access_token))
            #raise ValidationError(orders_url)
            res = requests.get(orders_url)
            res = res.json()[filtro]
            return res



    @api.model
    def check_categories(self,id ,  server , parent):
        cat_id = None
        existe = self.env['product.public.category'].search([('id_app', '=', str(id)),('server_meli','=',int(server.id))])
        if existe:
            cat_id = existe
        else:
            #buscar la data en el woocommerce
            #cwoo = wcapi.get("products/categories/"+str(id)).json()
            cwoo = 0
            category_url = '{}/categories/{}'.format(API_URL, id)
            #raise ValidationError(category_url)
            cwoo = requests.get(category_url).json()
            #name_categor = res.json()['name']
            #crear la categoria

            json = self.json_fields(cwoo,'categories',server)
            #pro = self.env['product.public.category'].create(json['create'])
            if not parent:
                parent = 'NULL'
            self.env.cr.execute("INSERT INTO product_public_category(name,id_app,server_meli,parent_id)"
                                " VALUES ('{}','{}',{},{})".format(json['create']['name'],id,server.id,parent))
            pro = self.env['product.public.category'].search([('id_app', '=', str(id)),
                                                                 ('server_meli','=',int(server.id))])

            cat_id = pro
        return  cat_id


    @api.model
    def insert_questions(self,exist,server):
        questions_url = '{}/questions/search?item_id={}&access_token={}'.format(API_URL,str(exist.id_app),str(server.access_token))
        res = requests.get(questions_url)
        res = res.json()
        questions = res['questions']
        for question in questions:
            existq = self.env['meli.questions'].search([('question_id', '=', question['id']), ('server_meli', '=', int(server.id))])
            question['product_id'] = exist.id
            json = self.json_fields(question, 'questions', server)

            if not  existq:
                existq = self.env['meli.questions'].create(json['create'])
            else:
                existq.write(json['write'])


    @api.model
    def check_produc(self,id ,server):
        pro_id = None
        existe = self.env['product.template'].search([(id_api, '=', str(id)),(server_api,'=',int(server.id))])
        if existe:
            pro_id = existe
        else:
            #buscar la data en mercado libre
            pwoo = None
            item_url = '{}/items?ids={}&access_token={}'.format(API_URL,id,server.access_token)
            #raise ValidationError(item_url)
            item = requests.get(item_url).json()
            json = self.json_fields(item[0],'products',server)
            pro = self.env['product.template'].create(json['create'])
            #insertar los atributos y variantes
            self.check_imagenes(item[0]['body']['pictures'],server,pro)
            self.insert_variations(item[0]['body'],server,pro)
            self.insert_questions(pro,server)

            pro_id = pro
        return  pro_id

    @api.model
    def check_product_order(self,p  , server):
        #raise ValidationError('jaaa')
        pp = None
        atributo = p['variation_id']
        #condicion para verificar si es un atributo
        if  atributo:
            #raise ValidationError(atributo)
            #buscar en product product
            pp = self.env['product.product'].search([('id_vex_varition','=',int(atributo)),('server_vex','=',int(server.id)),])
            #si no existe crearlo
            if not pp:
                self.check_produc(p['id'], server)
                pp = self.env['product.product'].search([('id_vex_varition', '=', int(atributo)),('server_vex', '=', int(server.id))])
        else:
            pt = self.check_produc(p['id'],  server)
            #raise ValidationError('jooo')
            #raise ValidationError(pt.product_variant_ids)

            pp = self.env['product.product'].search([('product_tmpl_id', '=', int(pt.id))])
        return  pp

    @api.model
    def insert_lines(self,lines,server,creado):
        amount_untaxed = amount_tax = 0.0
        for p in lines:
            #raise ValidationError(p['quantity'])
            existe = self.check_product_order(p['item'] ,server)
            #raise ValidationError(existe)
            new_line = {
                                    'name':'line_'+str(existe.id),
                                    'product_id': existe.id,
                                    'product_uom_qty': int(p['quantity']),
                                    'price_unit': float(p['unit_price'])-float(p['sale_fee'])  ,
                                    'order_id': creado.id,
                                    #'price_subtotal': p['subtotal'],
                                    'price_tax': 0.0,
                                    #'price_total': p['subtotal'],
                                    'tax_id': None,
                                    #campos requeridos
                                    'customer_lead':1.0,
                                }
            creado.order_line += self.env['sale.order.line'].new(new_line)
            #raise ValidationError(creado.order_line)
            amount_untaxed += (float(p['unit_price'])-float(p['sale_fee']))*int(p['quantity'])


        creado.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': amount_tax,
                                'amount_total': amount_untaxed + amount_tax,
                            })

    @api.model
    def for_child(self,childrens,server,parent):
        if childrens:
            for child in childrens:
                c = self.check_categories(child['id'],server,parent.id)
                #category_url = '{}/categories/{}'.format(API_URL, str(c.id_app))
                #childchild = requests.get(category_url).json()
                #self.for_child(childchild['children_categories'],server,c)

    @api.model
    def insert_categorias_children(self,id,server,parent):
        categories_url =  "https://api.mercadolibre.com/categories/{}".format(str(id))
        res = requests.get(categories_url).json()
        if 'children_categories' in res:
            self.for_child(res['children_categories'],server,parent)


    @api.model
    def synchronize(self, api, action, server):
        query = str(action.argument)
        table = str(action.model)

        self.check_synchronize(server)

        data_request = self.meli_api(server , query , 'results')
        #import json
        #raise ValidationError(json.dumps(data_request))
        for dr in data_request:
            if query == "products":
                dr = dr[0]
            #import json
            #raise ValidationError(json.dumps(dr))
            if query == "products" and  server.import_products_paused == False:
                if  dr['body']['status'] != 'active':
                    continue
            #import json
            #raise ValidationError(json.dumps(dr[0]['body']['id']))
            #raise ValidationError(json.dumps(dr['body']['id']))
            id_appx = dr['body']['id'] if query == "products" else dr['id']
            exist = self.env[table].search([('id_app', '=', str(id_appx)), ('server_meli', '=', int(server.id))])
            json = self.json_fields(dr, query, server)
            if not  exist:
                #raise ValidationError(json)
                exist = self.env[table].create(json['create'])
                if query == "orders":
                    self.insert_lines(dr['order_items'],server,exist)

            else:
                #raise ValidationError('f')
                exist.write(json['write'])

            if query == "products":
                self.check_imagenes(dr['body']['pictures'],server,exist)
                self.insert_variations(dr['body'],server,exist)
                self.insert_questions(exist,server)
            if query == 'categories':
                self.insert_categorias_children(dr['id'],server,exist)

    @api.model
    def sync_start(self, server, action):
        print("serveeeer", server, action)
        if server:
            self.synchronize(None, action, server)

    def start_start(self, argument):
        accion = self.env['meli.action.list'].search([('argument', '=', argument)])
        print("acccciooon", accion)
        if accion:
            servers = self.env['meli.synchro.instance'].search([('active_automatic', '=', True)])
            print("serveeeeers", servers)
            for server in servers:
                start_date = fields.Datetime.now()
                threaded_synchronization = threading.Thread(target=self.sync_start(server, accion))
                threaded_synchronization.run()
                end_date = fields.Datetime.now()
                accion.log += self.env['meli.logs'].new({
                    'start_date': start_date,
                    'end_date': end_date,
                    'description': 'Syncro Automatic',
                    'state': 'done',
                    'server': server.id
                })

    # sincronizar un producto
    def start_sync_products(self):
        self.start_start('products')

    def start_sync_orders(self):
        self.start_start('orders')
