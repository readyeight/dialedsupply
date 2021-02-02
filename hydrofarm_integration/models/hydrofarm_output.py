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


class HydroFarmImportData(models.Model):
    _name = 'hydrofarm.outputs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HydroFarm Outputs'

    connection_id = fields.Many2one('hydrofarm.vendor', string='Connection')
    name = fields.Char(string="Name")
    sku = fields.Char(string="Sku")
    product_id = fields.Many2one('product.template',string='Product')

    recid = fields.Char(string="recid")
    namealias = fields.Char(string="namealias")
    categoryid = fields.Char(string="categoryid")
    description = fields.Char(string="description")
    webdescription = fields.Char(string="webdescription")
    unitsize = fields.Char(string="unitsize")
    model = fields.Char(string="model")
    isdefault = fields.Char(string="isdefault")
    isdiscontinued = fields.Char(string="isdiscontinued")
    isspecialorder = fields.Char(string="isspecialorder")
    isbuildtoorder = fields.Char(string="isbuildtoorder")
    isclearance = fields.Char(string="isclearance")

    issale = fields.Char(string="issale")
    ishazmat = fields.Char(string="ishazmat")
    freightrestricted = fields.Char(string="freightrestricted")
    freightquoterequired = fields.Char(string="freightquoterequired")
    defaultuom = fields.Char(string="defaultuom")
    defaultuomrecid = fields.Char(string="defaultuomrecid")
    defaultimageid = fields.Char(string="defaultimageid")
    mixmatchgrp = fields.Char(string="mixmatchgrp")
    warranty = fields.Char(string="warranty")
    trackingdimensiongroup = fields.Char(string="trackingdimensiongroup")
    launchdate = fields.Char(string="launchdate")
    salestartdate = fields.Char(string="salestartdate")

    saleenddate = fields.Char(string="saleenddate")
    modifiedon = fields.Char(string="modifiedon")
    createdon = fields.Char(string="createdon")



    image = fields.Char(string="image")
    height = fields.Char(string="height")
    width = fields.Char(string="width")
    depth = fields.Char(string="depth")
    volume = fields.Char(string="depth")

    # wholesalePrice = fields.Char(string="wholesalePrice")
    dimensions = fields.Char(string="dimensions")
    # trackingdimensiongroup = fields.Char(string="trackingdimensiongroup")
    # launchdate = fields.Char(string="launchdate")
    # salestartdate = fields.Char(string="salestartdate")
    keyword = fields.Char(string="KeyWord")
    page_size = fields.Char(string="Page Size")
    page_no = fields.Char(string="Page Number")
    # loop_i = fields.Integer(string="Page Number",default=0)
    retailPrice = fields.Char(string='retailPrice')
    yourPrice_ids = fields.One2many('your.price','price_id',string='Your Prices',ondelete='cascade')



