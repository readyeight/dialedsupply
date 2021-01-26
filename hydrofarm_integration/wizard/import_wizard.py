import pdb

from odoo import models,fields,_
import json
import requests
import logging
logger = logging.getLogger(__name__)
TIMEOUT = 100
import base64
from odoo.exceptions import UserError, ValidationError



class ImportData(models.TransientModel):
    _name = 'import.data'


    def _get_outputs(self):
        if self._context.get('default_product_out'):
            return self.env['hydrofarm.outputs'].search([('id', 'in',self._context.get('default_product_out'))])


    fetched_ids = fields.Many2many('hydrofarm.outputs',
                                   'hydrofarm_group_rel', string="OutPut", default=lambda self: self._get_outputs(),
                                   required=True)

    def import_data(self):
        products_view = self.env['product.template']
        self.ensure_one()
        hydrofarm = self.env['hydrofarm.vendor'].search([('active', '=', True)], limit=1)
        request_url = hydrofarm.access_token_url
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = {
            'scope': "hydrofarmApi read write",
            'client_id': hydrofarm.client_id,
            'client_secret': hydrofarm.client_secret,
            'grant_type': "client_credentials"
        }
        print("=================================================================")

        try:

            for prd in self.fetched_ids.filtered(lambda line: line.check_box == True):

                vendor = self.env['res.partner'].search(
                    [('name', '=', hydrofarm.partner.name), ('is_api_vendor', '=', True)])
                if vendor:
                    vendor_mapping = self.env['vendor.mapping'].search([('vendor', '=', vendor.id)])
                    if vendor_mapping:
                        mapping_product_name = self.env['vendor.mapping'].search(
                            [('vendor', '=', vendor.id), ('vendor_api_ref', '=', 'name')], limit=1)
                        product_obj = self.env['product.template'].search(
                            [(mapping_product_name.odoo_api_field_ref.name, '=', prd.name)])
                        if not product_obj:
                            vendor_mapping1 = self.env['vendor.mapping'].search([('vendor', '=', vendor.id),
                                                                                 ('odoo_api_model_ref.name', "not in",
                                                                                  ['Supplier Pricelist'])
                                                                                 ])
                            print(vendor_mapping1, 'vendor_mapping1')
                            general_my_dict = {}
                            for line1 in vendor_mapping1:
                                if line1.vendor_api_ref == 'name':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: prd.name})
                                if line1.vendor_api_ref == 'sku':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: prd.sku})
                                if line1.vendor_api_ref == 'description':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: prd.description})
                                hydrofarm_categ = self.env['hydro.categorie'].search(
                                    [('categ_id', '=', str(prd.categoryid))], limit=1)
                                if not hydrofarm_categ:
                                    raise ValidationError(_('You Have to fetch categories First.'))
                                product_category = self.env['product.category'].create(
                                    {'name': hydrofarm_categ.name})
                                if line1.vendor_api_ref == 'categoryid':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: product_category.id})

                                if line1.vendor_api_ref == 'image':
                                    img = prd.image
                                    if img != False:
                                        image = base64.b64encode(requests.get(img.strip()).content).replace(b'\n', b'')
                                        print(image, 'image')
                                        general_my_dict.update({line1.odoo_api_field_ref.name: image})
                                if line1.vendor_api_ref == 'retailPrice':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: prd.retailPrice})
                                if line1.vendor_api_ref == 'volume':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.volume)})
                                if line1.vendor_api_ref == 'unitsize':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.unitsize)})
                                if line1.vendor_api_ref == 'height':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.height)})
                                if line1.vendor_api_ref == 'width':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.width)})
                                if line1.vendor_api_ref == 'depth':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.depth)})

                            product_obj = self.env['product.template'].sudo().create(general_my_dict)
                            products_view += product_obj

                    product_template = products_view.search(
                        [('name', '=', prd.name)], limit=1)
                    if product_template:
                        for attribute in prd.yourPrice_ids:
                            print(prd.yourPrice_ids, 'prd.yourPrice_ids')
                            product_exists_supplier = self.env['product.supplierinfo'].search(
                                [('name', '=', vendor.id),
                                 ('product_id', '=', product_template.product_variant_id.id),
                                 ('min_qty', '=', float(attribute.qtyStart)),
                                 ], limit=1)
                            if not product_exists_supplier:
                                product_exists_supplier = self.env['product.supplierinfo'].create({
                                    'name': vendor.id,
                                    'product_id': product_template.product_variant_id.id,
                                    'product_tmpl_id': product_template.id
                                })
                            product_exists_supplier.write({
                                'price': attribute.yourprice,
                                'min_qty': attribute.qtyStart,
                            })

            print(products_view.ids)
            return {
                'domain': [('id', 'in', products_view.ids)],
                'name': _('Products'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'product.template',
                'view_id': False,
                'type': 'ir.actions.act_window'
            }

        except requests.HTTPError:
            print("hiiiiiiisdfasfasdfasdfasfasiiiiiiiiiiiii")





class ImportSelectedData(models.TransientModel):
    _name = 'import.selected.data'


    def _get_outputs(self):
        if self._context.get('default_product_out'):
            return self.env['hydrofarm.outputs'].search([('id', 'in',self._context.get('default_product_out'))])


    fetched_ids = fields.Many2many('hydrofarm.outputs',
                                   'hydrofarm_group_selected_rel', string="OutPut", default=lambda self: self._get_outputs(),
                                   required=True)



    def import_selected_data(self):
        products_view = self.env['product.template']
        self.ensure_one()
        hydrofarm = self.env['hydrofarm.vendor'].search([('active', '=', True)], limit=1)
        request_url = hydrofarm.access_token_url
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = {
            'scope': "hydrofarmApi read write",
            'client_id': hydrofarm.client_id,
            'client_secret': hydrofarm.client_secret,
            'grant_type': "client_credentials"
        }
        print("=================================================================")

        try:
            for prd in self.fetched_ids:


                vendor = self.env['res.partner'].search([('name', '=', hydrofarm.partner.name), ('is_api_vendor', '=', True)])
                if vendor:
                    vendor_mapping = self.env['vendor.mapping'].search([('vendor', '=', vendor.id)])
                    if vendor_mapping:
                        mapping_product_name = self.env['vendor.mapping'].search([('vendor', '=', vendor.id),('vendor_api_ref', '=', 'name')],limit=1)
                        product_obj = self.env['product.template'].search([(mapping_product_name.odoo_api_field_ref.name, '=', prd.name)])
                        if not product_obj:
                            vendor_mapping1 = self.env['vendor.mapping'].search([('vendor', '=', vendor.id),
                                                                                 ('odoo_api_model_ref.name' ,"not in", ['Supplier Pricelist'])
                                                                                ])
                            print(vendor_mapping1,'vendor_mapping1')
                            general_my_dict = {}
                            for line1 in vendor_mapping1:
                                if line1.vendor_api_ref == 'name':
                                    general_my_dict.update({line1.odoo_api_field_ref.name : prd.name})
                                if line1.vendor_api_ref == 'sku':
                                    general_my_dict.update({line1.odoo_api_field_ref.name : prd.sku})
                                if line1.vendor_api_ref == 'description':
                                    general_my_dict.update({line1.odoo_api_field_ref.name : prd.description})
                                hydrofarm_categ = self.env['hydro.categorie'].search(
                                    [('categ_id', '=', str(prd.categoryid))], limit=1)
                                if not hydrofarm_categ:
                                    raise ValidationError(_('You Have to fetch categories First.'))
                                product_category = self.env['product.category'].create(
                                    {'name': hydrofarm_categ.name})
                                if line1.vendor_api_ref == 'categoryid':

                                    general_my_dict.update({line1.odoo_api_field_ref.name : product_category.id})

                                if line1.vendor_api_ref == 'image':
                                    img = prd.image
                                    if img != False:
                                        image = base64.b64encode(requests.get(img.strip()).content).replace(b'\n', b'')
                                        print(image, 'image')
                                        general_my_dict.update({line1.odoo_api_field_ref.name: image})
                                if line1.vendor_api_ref == 'retailPrice':
                                    general_my_dict.update({line1.odoo_api_field_ref.name : prd.retailPrice})
                                if line1.vendor_api_ref == 'volume':
                                    general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.volume)})
                                if line1.vendor_api_ref == 'unitsize':
                                    general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.unitsize)})
                                if line1.vendor_api_ref == 'height':
                                    general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.height)})
                                if line1.vendor_api_ref == 'width':
                                    general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.width)})
                                if line1.vendor_api_ref == 'depth':
                                    general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.depth)})

                            product_obj = self.env['product.template'].sudo().create(general_my_dict)
                            products_view += product_obj

                    product_template = products_view.search(
                        [('name', '=', prd.name)],limit=1)
                    if product_template:
                        for attribute in prd.yourPrice_ids:
                            print(prd.yourPrice_ids,'prd.yourPrice_ids')
                            product_exists_supplier = self.env['product.supplierinfo'].search(
                                [('name', '=', vendor.id),
                                 ('product_id', '=', product_template.product_variant_id.id),
                                 ('min_qty', '=', float(attribute.qtyStart)),
                                 ], limit=1)
                            if not product_exists_supplier:
                                product_exists_supplier = self.env['product.supplierinfo'].create({
                                    'name': vendor.id,
                                    'product_id': product_template.product_variant_id.id,
                                    'product_tmpl_id': product_template.id
                                })
                            product_exists_supplier.write({
                                'price': attribute.yourprice,
                                'min_qty': attribute.qtyStart,
                            })


            print(products_view.ids)
            return {
                'domain': [('id', 'in', products_view.ids)],
                'name': _('Products'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'product.template',
                'view_id': False,
                'type': 'ir.actions.act_window'
            }

        except requests.HTTPError:
            print("hiiiiiiisdfasfasdfasdfasfasiiiiiiiiiiiii")




class HydroFarmImportData(models.Model):
    _name = 'hydrofarm.outputs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HydroFarm Outputs'


    name = fields.Char(string="Name")
    sku = fields.Char(string="Sku")
    check_box = fields.Boolean(string='Select')

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



class HydroFarmyourprice(models.Model):
    _name = 'your.price'
    _description = 'your.price'


    yourprice = fields.Char(string="yourprice")
    price = fields.Char(string="price")
    qtyStart = fields.Char(string="qtyStart")
    qtyEnd = fields.Char(string="qtyEnd")
    price_id = fields.Many2one('hydrofarm.outputs',string='price_id')
