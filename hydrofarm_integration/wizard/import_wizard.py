import pdb

from odoo import models,fields,_
import json
import requests
import logging
logger = logging.getLogger(__name__)
TIMEOUT = 100
import base64
from odoo.exceptions import UserError, ValidationError
import PIL
import urllib
from odoo.tools import image as mg
# from io import BytesIO
import os




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

        try:
            for prd in self.fetched_ids:

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
                            general_my_dict = {}
                            for line1 in vendor_mapping1:
                                if line1.vendor_api_ref == 'name':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: prd.name})
                                if line1.vendor_api_ref == 'sku':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: prd.sku})
                                if line1.vendor_api_ref == 'description':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: prd.description})
                                if prd.categoryid != False:
                                    hydrofarm_categ = self.env['hydro.category'].search(
                                        [('categ_id', '=', str(prd.categoryid))], limit=1)
                                    if hydrofarm_categ:
                                        # raise ValidationError(_('You Have to fetch categories First.'))
                                        product_category = self.env['product.category'].search(
                                            [('name', '=', hydrofarm_categ.name)], limit=1)
                                        if not product_category:
                                            product_category = self.env['product.category'].create(
                                                {'name': hydrofarm_categ.name})
                                        product_public_category = self.env['product.public.category'].search(
                                            [('name', '=', hydrofarm_categ.name)], limit=1)
                                        if not product_public_category:
                                            product_public_category = self.env['product.public.category'].create(
                                                {'name': hydrofarm_categ.name})

                                        if line1.vendor_api_ref == 'categoryid':
                                            general_my_dict.update(
                                                {line1.odoo_api_field_ref.name: product_category.id or False})
                                            general_my_dict.update(
                                                {'public_categ_ids': [(4, product_public_category.id)] or False})
                                            # [[4, [product_public_category.id]]]

                                if line1.vendor_api_ref == 'image':
                                    img = prd.image
                                   
                                    if img != False:
                                        image = base64.b64encode(requests.get(img.strip()).content).replace(b'\n', b'')
                                        general_my_dict.update({line1.odoo_api_field_ref.name: image})
                                if line1.vendor_api_ref == 'retailPrice':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: prd.retailPrice})
                                if line1.vendor_api_ref == 'volume':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.volume or 0.0)})
                                if line1.vendor_api_ref == 'unitsize':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.unitsize or 0.0)})
                                if line1.vendor_api_ref == 'height':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.height or 0.0)})
                                if line1.vendor_api_ref == 'width':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.width or 0.0)})
                                if line1.vendor_api_ref == 'depth':
                                    general_my_dict.update({line1.odoo_api_field_ref.name: float(prd.depth or 0.0)})

                            product_obj = self.env['product.template'].sudo().create(general_my_dict)
                            products_view += product_obj
                            prd.product_id = product_obj

                    product_template = products_view.search(
                        [('name', '=', prd.name)], limit=1)
                    if product_template:
                        for attribute in prd.yourPrice_ids:
                            # print(prd.yourPrice_ids, 'prd.yourPrice_ids')
                            if attribute.qtyStart != False:
                                product_exists_supplier = self.env['product.supplierinfo'].search(
                                    [('name', '=', vendor.id),
                                     ('product_id', '=', product_template.product_variant_id.id),
                                     ('min_qty', '=', float(attribute.qtyStart or 0.0)),
                                     ], limit=1)
                                if not product_exists_supplier:
                                    product_exists_supplier = self.env['product.supplierinfo'].create({
                                        'name': vendor.id,
                                        'product_id': product_template.product_variant_id.id,
                                        'product_tmpl_id': product_template.id
                                    })
                                product_exists_supplier.write({
                                    'price': attribute.yourprice,
                                    'min_qty': float(attribute.qtyStart or 0.0) or 0.0,
                                })

            # print(products_view.ids)
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
        if (len(self.fetched_ids)< 501):
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
                                # print('vendor_mapping1 my ',vendor_mapping1)
                                general_my_dict = {}
                                for line1 in vendor_mapping1:
                                    if line1.vendor_api_ref == 'name':
                                        general_my_dict.update({line1.odoo_api_field_ref.name : prd.name})
                                    if line1.vendor_api_ref == 'sku':
                                        general_my_dict.update({line1.odoo_api_field_ref.name : prd.sku})
                                    if line1.vendor_api_ref == 'description':
                                        general_my_dict.update({line1.odoo_api_field_ref.name : prd.description})
                                    if prd.categoryid != False:
                                        hydrofarm_categ = self.env['hydro.category'].search(
                                            [('categ_id', '=', str(prd.categoryid))], limit=1)
                                        if hydrofarm_categ:
                                            # raise ValidationError(_('You Have to fetch categories First.'))
                                            product_category = self.env['product.category'].search(
                                                [('name', '=', hydrofarm_categ.name)], limit=1)
                                            if not product_category:
                                                product_category = self.env['product.category'].create(
                                                    {'name': hydrofarm_categ.name})
                                            product_public_category = self.env['product.public.category'].search(
                                                [('name', '=', hydrofarm_categ.name)], limit=1)
                                            if not product_public_category:
                                                product_public_category = self.env['product.public.category'].create(
                                                    {'name': hydrofarm_categ.name})

                                            if line1.vendor_api_ref == 'categoryid':
                                                general_my_dict.update({line1.odoo_api_field_ref.name: product_category.id or False})
                                                general_my_dict.update({'public_categ_ids': [(4, product_public_category.id)] or False})
                                                # [[4, [product_public_category.id]]]



                                    if line1.vendor_api_ref == 'image':
                                        img = prd.image
                                        if img != False:
                                            strr=str(img)
                                            n=strr.split("/",-1)
                                            jpg=urllib.request.urlretrieve(str(img), str(n[-1]))
                                            f = PIL.Image.open(str(n[-1]))
                                            w,h=f.size

                                            if w * h > mg.IMAGE_MAX_RESOLUTION:
                                                image=False
                                                
                                                # fn='new11_.jpg'
                                                # b=f.resize((int(1024),int(768)),PIL.Image.ANTIALIAS)
                                                # sv=f.save(fn,optimize=True,quality=50)
                                                # t = PIL.Image.open(fn)
                                                # fo = PIL.Image.open(fn).tobytes()
                                                
                                                # 
                                                # image=base64.b64encode(requests.get(img.strip()).content).replace(b'\n', b'')
                                                # resize_image = tools.image_resize_image(c, size=(250, 250), avoid_if_small=True)
                                                # image = resize_image
                                                    
                                            else:

                                                image=base64.b64encode(requests.get(img.strip()).content).replace(b'\n', b'')

                                            os.unlink(str(n[-1]))
                                            general_my_dict.update({line1.odoo_api_field_ref.name: image})

                                    if line1.vendor_api_ref == 'retailPrice':
                                        general_my_dict.update({line1.odoo_api_field_ref.name : prd.retailPrice})
                                    if line1.vendor_api_ref == 'volume':
                                        general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.volume or 0.0)})
                                    if line1.vendor_api_ref == 'unitsize':
                                        general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.unitsize or 0.0)})
                                    if line1.vendor_api_ref == 'height':
                                        general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.height or 0.0)})
                                    if line1.vendor_api_ref == 'width':
                                        general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.width or 0.0)})
                                    if line1.vendor_api_ref == 'depth':
                                        general_my_dict.update({line1.odoo_api_field_ref.name : float(prd.depth or 0.0)})

                                product_obj = self.env['product.template'].sudo().create(general_my_dict)
                                prd.product_id = product_obj
                            products_view += product_obj

                        product_template = products_view.search(
                            [('name', '=', prd.name)],limit=1)
                        if product_template:
                            for attribute in prd.yourPrice_ids:
                                # print(prd.yourPrice_ids,'prd.yourPrice_ids')
                                if attribute.qtyStart != False:
                                    product_exists_supplier = self.env['product.supplierinfo'].search(
                                        [('name', '=', vendor.id),
                                        ('product_id', '=', product_template.product_variant_id.id),
                                        ('min_qty', '=', float(attribute.qtyStart or 0.0)),
                                        ], limit=1)
                                    if not product_exists_supplier:
                                        product_exists_supplier = self.env['product.supplierinfo'].create({
                                            'name': vendor.id,
                                            'product_id': product_template.product_variant_id.id,
                                            'product_tmpl_id': product_template.id
                                        })
                                    product_exists_supplier.write({
                                        'price': attribute.yourprice,
                                        'min_qty': float(attribute.qtyStart or 0.0) or 0.0,
                                    })


                # print(products_view.ids)
                return {
                    'domain': [('id', 'in', products_view.ids)],
                    'name': _('Products'),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'product.template',
                    'view_id': False,
                    'type': 'ir.actions.act_window'
                }


            # except requests.HTTPError:
            except Exception as e:
                print(e.args)
        raise ValidationError(_("Server not Allowed To Import Products Greater Than 500"))



class HydroFarmyourprice(models.Model):
    _name = 'your.price'
    _description = 'your.price'


    yourprice = fields.Char(string="yourprice")
    price = fields.Char(string="price")
    qtyStart = fields.Char(string="qtyStart")
    qtyEnd = fields.Char(string="qtyEnd")
    price_id = fields.Many2one('hydrofarm.outputs',string='price_id')
