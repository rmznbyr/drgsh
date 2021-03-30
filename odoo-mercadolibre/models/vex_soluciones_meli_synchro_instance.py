from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
import threading
from ..models.vex_soluciones_meli_config import API_URL, INFO_URL, get_token
# from ..wizard.vex_soluciones_meli_action_synchro import MeliActionSynchro
from .vex_soluciones_meli_config import AUTH_URL, get_token, COUNTRIES, CURRENCIES
from odoo.addons.payment.models.payment_acquirer import ValidationError
import requests


class ApiSynchroInstance(models.Model):
    _inherit  = 'vex.instance'
    name      = fields.Char(required=True)

    app_id = fields.Char(string="App ID")
    user_id = fields.Char(string="User ID")
    secret_key = fields.Char()
    server_code = fields.Char()
    redirect_uri = fields.Char(default="https://www.mercadolibre.com.pe")
    access_token = fields.Char()
    refresh_token = fields.Char()

    meli_country = fields.Selection(COUNTRIES, string='Country')
    default_currency = fields.Selection(CURRENCIES, string='Default Currency')
    
    nick = fields.Char()    
    import_products_paused = fields.Boolean(default=False)
    conector         = fields.Selection(selection_add=[('meli', 'Mercado Libre')])
    

    def get_user(self):
        if not self.nick:
            raise ValidationError('NOT NICK')
        if not self.meli_country:
            raise ValidationError('NOT COUNTRY')
        url_user = "https://api.mercadolibre.com/sites/{}/search?nickname={}".format(self.meli_country, self.nick)
        item = requests.get(url_user).json()
        if 'seller' in item:
            self.user_id = str(item['seller']['id'])
        else:
            raise ValidationError('INCORRECT NICK OR COUNTRY')

    def get_token(self):
        if not self.server_code:
            raise ValidationError('NOT SERVER CODE')
        if not self.app_id:
            raise ValidationError('Not App ID')
        if not self.secret_key:
            raise ValidationError('Not secret key')
        if not self.redirect_uri:
            raise ValidationError('Not Redirect Uri')
        headers = {"accept": "application/json",
                   "content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "authorization_code",
            "client_id": self.app_id,
            "client_secret": self.secret_key,
            "code": self.server_code,
            "redirect_uri": self.redirect_uri,
        }
        url = 'https://api.mercadolibre.com/oauth/token'
        r = requests.post(url, json=data, headers=headers)
        data = r.json()

        if 'access_token' in data:
            self.write({
                'access_token': data['access_token'],
                'refresh_token': data['refresh_token'],
            })
        else:
            import json
            raise ValidationError(json.dumps(data))

   

    def fun_test(self):
        res = super(ApiSynchroInstance, self).fun_test()
        if self.conector == 'meli':
            self.test_run()
        return res

    def test_run(self):

        access_token = self.access_token
        user_info_url = 'https://api.mercadolibre.com/users/me'
        res = requests.get(user_info_url, params={'access_token': access_token})

        if res.status_code == 200:
            raise ValidationError('Successfully connected')
        else:
            self.env['vex.synchro'].check_synchronize(self)
