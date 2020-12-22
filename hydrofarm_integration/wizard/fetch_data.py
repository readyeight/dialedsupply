from odoo import models,fields,_
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
import requests
import logging
logger = logging.getLogger(__name__)
from xml.etree import ElementTree as ET
import json
from odoo.tools import float_compare, float_round

TIMEOUT = 100



class FetchData(models.TransientModel):
    _name = 'fetch.data'

    keyword = fields.Char(string="KeyWord")

    def fetch_data(self):
        self.ensure_one()
        hydrofarm = self.env['hydrofarm.vendor'].search([('active', '=', True)], limit=1)
        request_url = hydrofarm.access_token_url
        print(request_url)
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = {
            'scope': "hydrofarmApi read write",
            'client_id': hydrofarm.client_id,
            'client_secret': hydrofarm.client_secret,
            'grant_type': "client_credentials"
        }

        # print(data,"data")
        try:
            print(request_url,data,headers,TIMEOUT)
            req = requests.post(request_url, data=data, headers=headers, timeout=100)
            # req = requests.post('https://oauth.hydrofarm.com/connect/token', data={'scope': 'hydrofarmApi read write',
            #                                                                        'client_id': '7200-13316-9cc1987d-88fb-4d12-be7d-850e953e79b1',
            #                                                                        'client_secret': '9245bc1b-48cb-404f-ad16-cfe88cd4f15c',
            #                                                                        'grant_type': 'client_credentials'},
            #                     headers={"Content-type": "application/x-www-form-urlencoded"}, timeout=100)
            if not req:
                raise ValidationError(_('Data is can not be fetched.'))
            print('req1',req)
            req.raise_for_status()
            parents_dict = req.json()
            access_token = parents_dict.get('access_token')
            print(access_token,'access_token')
            url = hydrofarm.url + "/api/products/getProducts"
            req_headers = {
                'Content-Type': "application/json",
                'Authorization': "Bearer " + access_token,
            }
            request_data = {
                "keyword": self.keyword,
                "includeProductVariants": True
            }
            data = json.dumps(request_data)
            print(data,'dumps data')
            print(url,'url')
            req = requests.post(url, data=data, headers=req_headers, timeout=100)
            if not req:
                raise ValidationError(_('Connection failed! Data can not be fetched.'))
            print(req)
            req.raise_for_status()
            products_dict = req.json()
            print(products_dict,'products_dict')
            product_out = []
            for prd in products_dict:
                previous= self.env['hydrofarm.outputs'].search([('name','=',prd.get('name')),('sku','=',prd.get('sku'))])
                previous.unlink()
                # if not previous:
                product_out_put_ids = self.env['hydrofarm.outputs'].create({
                    'name': prd.get('name'),
                    'sku': prd.get('sku'),
                })
                product_out.append(product_out_put_ids.id)
            print(product_out,'product_out')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'import.data',
                'views': [[False, 'form']],
                'target': 'new',
                'context': {
                    'default_product_out': product_out,
                }
            }
            # form_view = self.env.ref('hydrofarm_integration.hydrofarm_outputs_tree_view')
            # tree_view = self.env.ref('hydrofarm_integration.hydrofarm_outputs_form_view')
            # return {
            #     # 'domain': [('id', 'in', product_out)],
            #     'name': _('Products'),
            #     # 'view_type': 'form',
            #     'view_mode': 'tree',
            #     'res_model': 'hydrofarm.outputs',
            #     'view_id': False,
            #     'views': [(tree_view and tree_view.id or False, 'tree')],
            #     # 'context': {'default_class_id': self.id},
            #     'type': 'ir.actions.act_window'
            # }
        except requests.HTTPError:
            raise ValidationError(_('The validation digit is not valid for "%s"'))
            # print("I M IEXCEPTIOn")
            # print('fetch data')
