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


class HydroCategory(models.Model):
    _name = "hydro.category"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'hydro.category'


    connection_id = fields.Many2one('hydrofarm.vendor',string='Connection')
    categ_id = fields.Char(string='ID')
    name = fields.Char(string='Name')
    shortName = fields.Char(string='Short Name')




