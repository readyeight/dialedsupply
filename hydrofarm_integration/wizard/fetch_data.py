from odoo import models,fields,_
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
import requests
import logging
logger = logging.getLogger(__name__)
from xml.etree import ElementTree as ET
import json
import base64
from odoo.tools import float_compare, float_round
import time

TIMEOUT = 100



class FetchData(models.TransientModel):
    _name = 'fetch.data'

    keyword = fields.Char(string="KeyWord")
    page_size = fields.Char(string="Page Size")
    page_no = fields.Char(string="Page Number")


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

        self.fetch_hydro_categories()
        try:


            print(request_url,data,headers,TIMEOUT)

            # self.close_action_cron()
            req = requests.post(request_url, data=data, headers=headers, timeout =10000)
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
                # "isSale": 1,
                # "pageSize": 48,
                # "pageNo": 0,
                # "includeProductVariants": True
                # "Categories" : 5637147054,
            }
            data = json.dumps(request_data)
            print(data,'dumps data')

            req = requests.post(url, data=data, headers=req_headers)
            if not req:
                raise ValidationError(_('Connection failed! Data can not be fetched.'))

            print(req)
            req.raise_for_status()
            products_dict = req.json()
            print(products_dict,'products_dict')
            product_out = []
            for prd in products_dict:
                hydrofarm = self.env['hydrofarm.outputs'].search([('recid', '=', prd.get('recid'))])
                if not hydrofarm:
                    retailPrice = prd.get('price').get('retailPrice')
                    wholesalePrice = prd.get('price').get('wholesalePrice')
                    price_list = []
                    for price_line in wholesalePrice:
                        values = {
                            'yourprice':str(price_line.get('yourPrice')),
                            'price': str(price_line.get('price')),
                            'qtyStart': str(price_line.get('qtyStart')),
                            'qtyEnd': str(price_line.get('qtyEnd'))

                        }
                        price_list.append([0,0,values])

                    values = {
                        "recid": prd.get('recid'),
                        "sku": prd.get('sku'),
                        "name": prd.get('name'),
                        "yourPrice_ids": price_list,
                        "retailPrice": retailPrice,
                        "namealias": prd.get('namealias'),
                        "categoryid": prd.get('categoryid'),
                        "description": prd.get('description'),
                        "webdescription": prd.get('webdescription'),
                        "unitsize": prd.get('unitsize'),
                        "model": prd.get('model'),
                        # "isdefault": prd.get('isdefault'),
                        # "isdiscontinued": prd.get('isdiscontinued'),
                        # "isspecialorder": prd.get('isspecialorder'),
                        # "isbuildtoorder": prd.get('isbuildtoorder'),
                        # "isclearance": prd.get('isclearance'),
                        # "issale": prd.get('issale'),
                        # "ishazmat": prd.get('ishazmat'),
                        # "freightrestricted": prd.get('freightrestricted'),
                        # "freightquoterequired": prd.get('freightquoterequired'),
                        # "defaultuom": prd.get('defaultuom'),
                        # "defaultuomrecid": prd.get('defaultuomrecid'),
                        # "defaultimageid": prd.get('defaultimageid'),
                        # "mixmatchgrp": prd.get('mixmatchgrp'),
                        # "warranty": prd.get('warranty'),
                        # "trackingdimensiongroup": prd.get('trackingdimensiongroup'),
                        # "launchdate": prd.get('launchdate'),
                        # "salestartdate": prd.get('salestartdate'),
                        # "saleenddate": prd.get('saleenddate'),
                        # "modifiedon": prd.get('modifiedon'),
                        # "createdon": prd.get('createdon'),
                        # "image": base64.b64encode(
                        #                         requests.get(
                        #                             prd.get('images')[0].get('url').strip()).content).replace(
                        #                         b'\n', b''),
                        "image": prd.get('images')[0].get('url') or False,
                        "height": prd.get('dimensions')[0].get('height'),
                        "width": prd.get('dimensions')[0].get('width'),
                        "depth": prd.get('dimensions')[0].get('depth'),
                        "volume" : float(prd.get('dimensions')[0].get('height')) *
                                                       float(prd.get('dimensions')[0].get('width')) *
                                                       float(prd.get('dimensions')[0].get('depth'))
                    }
                    product_out_put_ids = self.env['hydrofarm.outputs'].create(values)
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

        except requests.HTTPError:
            raise ValidationError(_('The validation digit is not valid for "%s"'))


    def fetch_products_data(self):
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
        self.fetch_hydro_categories()

        try:

            print(request_url, data, headers, TIMEOUT)

            req = requests.post(request_url, data=data, headers=headers, timeout=10000)

            if not req:
                raise ValidationError(_('Data is can not be fetched.'))

            parents_dict = req.json()
            access_token = parents_dict.get('access_token')
            url = hydrofarm.url + "/api/products/getProducts"
            req_headers = {
                'Content-Type': "application/json",
                'Authorization': "Bearer " + access_token,
            }

            request_data = {
                "fields": "recID sku name nameAlias categoryId sortPriority description webDescription unitSize Model images dimensions price",
            }
            payload = {'pageSize': -1}
            data = json.dumps(request_data)
            products_response = requests.post(url, headers=req_headers, data=data, params=payload, timeout=100000)
            if products_response.status_code == 200:
                products_dict = products_response.json()
                print(len(products_dict))
                print(products_dict)
                print(len(products_dict))


                product_out = []
                for prd in products_dict:
                    hydrofarm = self.env['hydrofarm.outputs'].search([('recid', '=', prd.get('recid'))])
                    if not hydrofarm:
                        retailPrice = prd.get('price').get('retailPrice')
                        wholesalePrice = prd.get('price').get('wholesalePrice')
                        print(prd.get('sku'),prd.get('name'))
                        print(wholesalePrice)
                        price_list = []
                        if wholesalePrice:
                            for price_line in wholesalePrice:
                                values = {
                                    'yourprice':str(price_line.get('yourPrice')),
                                    'price': str(price_line.get('price')),
                                    'qtyStart': str(price_line.get('qtyStart')),
                                    'qtyEnd': str(price_line.get('qtyEnd'))

                                }
                                price_list.append([0,0,values])

                        values = {
                            "recid": prd.get('recid'),
                            "sku": prd.get('sku'),
                            "name": prd.get('name'),
                            "yourPrice_ids": price_list,
                            "retailPrice": retailPrice,
                            "namealias": prd.get('namealias'),
                            "categoryid": prd.get('categoryid'),
                            "description": prd.get('description'),
                            "unitsize": prd.get('unitsize'),
                            "model": prd.get('model'),
                            "image":False,
                        }

                        image_list = prd.get('images')
                        if len(image_list) > 0:
                            values['image'] = prd.get('images')[0].get('url')
                        dimensions_list = prd.get('dimensions')
                        if len(dimensions_list) > 0:
                            values['height'] = prd.get('dimensions')[0].get('height'),
                            values['width'] = prd.get('dimensions')[0].get('width'),
                            values['depth'] = prd.get('dimensions')[0].get('depth'),
                            values['volume'] = float(prd.get('dimensions')[0].get('height')) *float(prd.get('dimensions')[0].get('width')) *float(prd.get('dimensions')[0].get('depth'))
                        product_out_put_ids = self.env['hydrofarm.outputs'].create(values)
                        product_out.append(product_out_put_ids.id)

                print(product_out,'product_out')
                # return {
                #     'domain': [('id', 'in', product_out)],
                #     'name': _('Hydrofarm Products'),
                #     'view_type': 'form',
                #     'view_mode': 'tree,form',
                #     'res_model': 'hydrofarm.outputs',
                #     'view_id': False,
                #     'views': [(self.env.ref('hydrofarm_integration.hydrofarm_outputs_tree_view').id, 'tree'),
                #               (self.env.ref('hydrofarm_integration.hydrofarm_outputs_form_view').id, 'form')],
                #     'type': 'ir.actions.act_window'
                # }
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'import.data',
                    'views': [[False, 'form']],
                    'target': 'new',
                    'context': {
                        'default_product_out': product_out,
                    }
                }

            else:
                raise ValidationError(_('Error in product Search!'))

        except requests.HTTPError:
            raise ValidationError(_('The validation digit is not valid for "%s"'))



    def fetch_hydro_categories(self):
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
        try:
            req = requests.post(request_url, data=data, headers=headers, timeout=10000)
            if not req:
                raise ValidationError(_('Data is can not be fetched.'))

            print('req1',req)
            req.raise_for_status()
            parents_dict = req.json()
            access_token = parents_dict.get('access_token')
            print(access_token,'access_token')
            url = hydrofarm.url + "/api/categories/getcategories"
            req_headers = {
                'Content-Type': "application/json",
                'Authorization': "Bearer " + access_token,
            }
            request_data = {
                # "keyword": self.keyword,
            }
            data = json.dumps(request_data)
            print(data,'dumps data')
            print(url,'url')

            req = requests.get(url, data=data, headers=req_headers, timeout =10000)
            if not req:
                raise ValidationError(_('Connection failed! Data can not be fetched.'))
            print(req)
            req.raise_for_status()
            products_dict = req.json()
            print(products_dict,'products_dict')
            for prd in products_dict:
                hydrofarm_categ = self.env['hydro.category'].search([('categ_id', '=', str(prd.get('id')))])
                hydrofarm_categ.unlink()
                if not hydrofarm_categ:
                    values = {
                        "categ_id": str(prd.get('id')),
                        "name": prd.get('name'),
                        "shortName": prd.get('shortName'),
                        "connection_id": hydrofarm.id

                    }
                    category_lines = self.env['hydro.category'].create(values)
                    print(category_lines,category_lines.name)

        except requests.HTTPError:
            raise ValidationError(_('The validation digit is not valid for "%s"'))



