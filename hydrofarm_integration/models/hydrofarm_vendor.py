# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, api, _
from odoo import http
from odoo.http import request
import requests
import logging

logger = logging.getLogger(__name__)
from xml.etree import ElementTree as ET
import json
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError, ValidationError
import base64

class HydroFarmApi(models.Model):
    _name = "hydrofarm.vendor"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'HydroFarm Vendor'

    partner = fields.Many2one('res.partner', string="Partner", required=True)
    url = fields.Char(string='Url', required=True)
    name = fields.Char(string='Name', required=True)
    client_id = fields.Char(string="Client ID", required=True)
    client_secret = fields.Char(string="Client Secret", required=True)
    access_token_url = fields.Char(string='Access Token Url', required=True)
    active = fields.Boolean(string="Active", default=True)
    message = fields.Char(string='Message')
    categories_ids = fields.One2many('hydro.category', 'connection_id', ondelete='cascade')
    product_ids = fields.One2many('hydrofarm.outputs', 'connection_id', ondelete='cascade')
    product_ids2 = fields.One2many('hydrofarm.outputs', 'connection_id', ondelete='cascade',
                                   domain=[('product_id', '!=', False)])

    # tested_date = fields.Datetime(string='Last Tested Date')
    product_url = fields.Char(string='Product Url', required=True)
    categories_url = fields.Char(string='Categories Url', required=True)

    # def _get_product_api(self):
    #     product_api = self.env['ir.cron'].search([('name', '=', 'Product API: Fetch All product')])
    #     if product_api:
    #         return product_api.id
    #     return True

    cron_id = fields.Many2one('ir.cron', string='Schedule Activity', readonly=1)
    interval_number = fields.Integer()
    interval_type = fields.Selection(string='Interval_type', selection=[('minutes', 'Minutes'),
                                                                        ('hours', 'Hours'), ('days', 'Days'),
                                                                        ('weeks', 'Weeks'), ('months', 'Months'), ],
                                     default="hours")
    run_date = fields.Datetime(string='Run Date', )
    cron_active = fields.Boolean(sting="Active", )

    @api.model
    def create(self, vals):
        res = super(HydroFarmApi, self).create(vals)
        model_id = self.env['ir.model'].search([('model', '=', self._name)])
        cron_values = {
            'name': "Cron get products " + (res.name or ""),
            'model_id': model_id and model_id.id,
            'state': 'code',
            'code': 'model.cron_product_api_update(' + str(res.id) + ')',
            'interval_number': res.interval_number,
            'interval_type': res.interval_type,
            'numbercall': -1,
            'active': res.cron_active,
        }
        cron = self.env['ir.cron'].sudo().create(cron_values)
        if cron:
            res.cron_id = cron.id
        return res

    @api.onchange('interval_number', 'interval_type', 'run_date', 'cron_active')
    def change_schedule_activity(self):
        if self.cron_id:
            if self.interval_number:
                self.cron_id.interval_number = self.interval_number
            if self.interval_type:
                self.cron_id.interval_type = self.interval_type
            if self.run_date:
                self.cron_id.nextcall = self.run_date
            self.cron_id.active = self.cron_active

    def cron_product_api_update(self,id):
        for rec in self.search([('id','=',int(id) )]):
            rec.get_products()


    def test_connection(self):
        self.ensure_one()
        request_url = self.access_token_url
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = {
            'scope': "hydrofarmApi read write",
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': "client_credentials"
        }
        response = requests.post(request_url, data=data, headers=headers, timeout=100)
        if response.status_code == 200:
            self.message = "Last Connection is Successful at" + " " + str(fields.Datetime.now())
            return response
        else:
            raise ValidationError(_('Connection is down/Not-Established.'))

    def get_products(self):
        response = self.test_connection()

        self.fetch_hydro_categories()

        parents_dict = response.json()
        access_token = parents_dict.get('access_token')
        url = self.url + self.product_url
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
                product_out_put_ids = self.env['hydrofarm.outputs'].search([('recid', '=', prd.get('recid')),('connection_id', '=', self.id)])
                if not product_out_put_ids:
                    retailPrice = prd.get('price').get('retailPrice')
                    wholesalePrice = prd.get('price').get('wholesalePrice')
                    print(prd.get('sku'), prd.get('name'))
                    print(wholesalePrice)
                    price_list = []
                    if wholesalePrice:
                        for price_line in wholesalePrice:
                            values = {
                                'yourprice': str(price_line.get('yourPrice')),
                                'price': str(price_line.get('price')),
                                'qtyStart': str(price_line.get('qtyStart')),
                                'qtyEnd': str(price_line.get('qtyEnd'))

                            }
                            price_list.append([0, 0, values])
                    # height = False
                    # width = False
                    # depth = False

                    values = {
                        "connection_id": self.id,
                        "recid": prd.get('recid'),
                        "sku": prd.get('sku'),
                        "name": prd.get('name'),
                        "yourPrice_ids": price_list,
                        "retailPrice": retailPrice,
                        "namealias": prd.get('namealias'),
                        "categoryid": prd.get('categoryid'),
                        "description": prd.get('description'),
                        # "webdescription": prd.get('webdescription'),
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
                        "image": False,
                        # "image":image,
                        # "height": prd.get('dimensions')[0].get('height'),
                        # "width": prd.get('dimensions')[0].get('width'),
                        # "depth": prd.get('dimensions')[0].get('depth'),
                        # "volume" : float(prd.get('dimensions')[0].get('height')) *
                        #                                float(prd.get('dimensions')[0].get('width')) *
                        #                                float(prd.get('dimensions')[0].get('depth'))
                    }

                    image_list = prd.get('images')
                    if len(image_list) > 0:
                        values['image'] = prd.get('images')[0].get('url')
                        # values['image'] = base64.b64encode(
                        #     requests.get(
                        #         prd.get('images')[0].get('url').strip()).content).replace(
                        #     b'\n', b'')
                    dimensions_list = prd.get('dimensions')
                    if len(dimensions_list) > 0:
                        values['height'] = prd.get('dimensions')[0].get('height'),
                        values['width'] = prd.get('dimensions')[0].get('width'),
                        values['depth'] = prd.get('dimensions')[0].get('depth'),
                        values['volume'] = float(prd.get('dimensions')[0].get('height')) * float(
                            prd.get('dimensions')[0].get('width')) * float(prd.get('dimensions')[0].get('depth'))
                    # print(prd.get('recid'))
                    # print(prd.get('images')[0].get('url') or False)
                    product_out_put_ids = self.env['hydrofarm.outputs'].create(values)
                product_out.append(product_out_put_ids.id)

            print(product_out, 'product_out')
            return {
                'domain': [('id', 'in', product_out)],
                'name': _('Hydrofarm Products'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'hydrofarm.outputs',
                'view_id': False,
                'views': [(self.env.ref('hydrofarm_integration.hydrofarm_outputs_tree_view').id, 'tree'),
                          (self.env.ref('hydrofarm_integration.hydrofarm_outputs_form_view').id, 'form')],
                # 'context': {'default_class_id': self.id},
                'type': 'ir.actions.act_window'
            }

        else:
            raise ValidationError(_('Error in product Search!'))

    def get_categories(self):
        response = self.test_connection()

        # req.raise_for_status()
        parents_dict = response.json()
        access_token = parents_dict.get('access_token')
        url = self.url + self.categories_url
        req_headers = {
            'Content-Type': "application/json",
            'Authorization': "Bearer " + access_token,
        }

        cat_response = requests.get(url, headers=req_headers, timeout=10000)

        if cat_response.status_code == 200:
            cat_dict = cat_response.json()
            print(len(cat_dict))
            print(cat_dict)
            # pdb.set_trace()
        else:
            raise ValidationError(_('Error in Categories Search!'))

    def fetch_hydro_categories(self):
        request_url = self.access_token_url
        print(request_url)
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = {
            'scope': "hydrofarmApi read write",
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': "client_credentials"
        }
        try:
            req = requests.post(request_url, data=data, headers=headers, timeout=10000)
            if not req:
                raise ValidationError(_('Data is can not be fetched.'))

            print('req1', req)
            req.raise_for_status()
            parents_dict = req.json()
            access_token = parents_dict.get('access_token')
            print(access_token, 'access_token')
            url = self.url + "/api/categories/getcategories"
            req_headers = {
                'Content-Type': "application/json",
                'Authorization': "Bearer " + access_token,
            }
            request_data = {
                # "keyword": self.keyword,
            }
            data = json.dumps(request_data)
            print(data, 'dumps data')
            print(url, 'url')

            req = requests.get(url, data=data, headers=req_headers, timeout=10000)
            if not req:
                raise ValidationError(_('Connection failed! Data can not be fetched.'))
            print(req)
            req.raise_for_status()
            products_dict = req.json()
            print(products_dict, 'products_dict')
            for prd in products_dict:
                hydrofarm_categ = self.env['hydro.category'].search([('categ_id', '=', str(prd.get('id')))])
                hydrofarm_categ.unlink()
                if not hydrofarm_categ:
                    values = {
                        "categ_id": str(prd.get('id')),
                        "name": prd.get('name'),
                        "shortName": prd.get('shortName'),
                        "connection_id": self.id

                    }
                    category_lines = self.env['hydro.category'].create(values)
                    print(category_lines, category_lines.name)

        except requests.HTTPError:
            raise ValidationError(_('The validation digit is not valid for "%s"'))
