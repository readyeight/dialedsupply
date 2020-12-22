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
    # tested_date = fields.Datetime(string='Last Tested Date')


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
        req = requests.post(request_url, data=data, headers=headers, timeout=100)
        # req = requests.post('https://oauth.hydrofarm.com/connect/token', data={'scope': 'hydrofarmApi read write',
        #                                                                        'client_id': '7200-13316-9cc1987d-88fb-4d12-be7d-850e953e79b1',
        #                                                                        'client_secret': '9245bc1b-48cb-404f-ad16-cfe88cd4f15c',
        #                                                                        'grant_type': 'client_credentials'},
        #                     headers={"Content-type": "application/x-www-form-urlencoded"}, timeout=100)
        print(req)
        if not req:
            raise ValidationError(_('Connection is down/Not-Established.'))



        req.raise_for_status()
        parents_dict = req.json()
        access_token = parents_dict.get('access_token')
        print(access_token, 'access_token')
        url = self.url + "/api/products/getProducts"
        req_headers = {
            'Content-Type': "application/json",
            'Authorization': "Bearer " + access_token,
        }
        request_data = {
            "keyword": 'PHB2010',
            "includeProductVariants": True
        }
        data = json.dumps(request_data)
        print(data, 'dumps data')
        print(url, 'url')
        req2 = requests.post(url, data=data, headers=req_headers, timeout=100)
        if req2:
            self.message = "Last Connection is Successful at" + " " + str(fields.Datetime.now())
        else:
            raise ValidationError(_('Connection is down/Not-Established.'))


