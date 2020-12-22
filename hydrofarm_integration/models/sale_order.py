# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import http
from odoo.http import request
import requests
import logging
logger = logging.getLogger(__name__)
from xml.etree import ElementTree as ET
import json
from odoo.tools import float_compare, float_round

TIMEOUT = 20

class HydroFarmApi(models.Model):
    _inherit = "sale.order"

    # def action_cancel(self):
