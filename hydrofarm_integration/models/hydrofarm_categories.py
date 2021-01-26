# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo import http
from odoo.http import request
import requests
import logging
logger = logging.getLogger(__name__)
from xml.etree import ElementTree as ET
import json
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError, ValidationError


class hydrofarm_categories(models.Model):
    _name = "hydrofarm.categories"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'hydrofarm_categories'
    _rec_name = 'name'


    categories_ids = fields.One2many('hydro.categorie','category_id',string='Categories',ondelete='cascade')
    name = fields.Char(string='Category',default='Category')


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

        # print(data,"data")
        try:
            # product_out = []
            # i = 1
            # finish_check = False
            # while finish_check==False:


            # print(request_url,data,headers,TIMEOUT)

            # self.close_action_cron()
            req = requests.post(request_url, data=data, headers=headers, timeout =10000)
            # req = requests.post('https://oauth.hydrofarm.com/connect/token', data={'scope': 'hydrofarmApi read write',
            #                                                                        'client_id': '7200-13316-9cc1987d-88fb-4d12-be7d-850e953e79b1',
            #                                                                        'client_secret': '9245bc1b-48cb-404f-ad16-cfe88cd4f15c',
            #                                                                        'grant_type': 'client_credentials'},
            #                     headers={"Content-type": "application/x-www-form-urlencoded"}, timeout=100)
            if not req:
                # print(i, 'i')
                raise ValidationError(_('Data is can not be fetched.'))

            print('req1',req)
            req.raise_for_status()
            parents_dict = req.json()
            access_token = parents_dict.get('access_token')
            print(access_token,'access_token')
            # pageno = str(i)
            # product_url = "/api/products/getProducts?pageSize=1&pageNo="+pageno
            # print(product_url)
            # ?pageSize = 1 & pageNo = 1
            # url = hydrofarm.url + "/api/products/getProducts?pageSize="+self.page_size+"&pageNo="+self.page_no
            url = hydrofarm.url + "/api/categories/getcategories"
            req_headers = {
                'Content-Type': "application/json",
                'Authorization': "Bearer " + access_token,
            }
            request_data = {
                # "keyword": self.keyword,
                # "isSale": 1,
                # "pageSize": 48,
                # "pageNo": 0,
                # "includeProductVariants": True
                # "Categories" : 5637147054,
            }
            data = json.dumps(request_data)
            print(data,'dumps data')
            print(url,'url')

            req = requests.get(url, data=data, headers=req_headers, timeout =10000)
            if not req:
                # print(i, 'i')
                finish_check = True
                raise ValidationError(_('Connection failed! Data can not be fetched.'))
            # else:

            print(req)
            req.raise_for_status()
            products_dict = req.json()
            print(products_dict,'products_dict')
            # product_out = []
            # categories_values=[]
            for prd in products_dict:
                hydrofarm_categ = self.env['hydro.categorie'].search([('categ_id', '=', str(prd.get('id')))])
                hydrofarm_categ.unlink()
                if not hydrofarm_categ:
                    values = {
                        "categ_id": str(prd.get('id')),
                        "name": prd.get('name'),
                        "shortName": prd.get('shortName'),
                        "category_id": self.id

                    }
                    category_lines = self.env['hydro.categorie'].create(values)
                    print(category_lines,category_lines.name)
                    # product_out.append(product_out_put_ids.id)

        except requests.HTTPError:
            raise ValidationError(_('The validation digit is not valid for "%s"'))

class hydro_categorie(models.Model):
    _name = "hydro.categorie"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'hydro.categorie'


    category_id = fields.Many2one('hydrofarm.categories',string='category main')
    categ_id = fields.Char(string='ID')
    name = fields.Char(string='Name')
    shortName = fields.Char(string='Short Name')




