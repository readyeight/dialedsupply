import pdb

from odoo import models,fields,_
import json
import requests
import logging
logger = logging.getLogger(__name__)
TIMEOUT = 100
import base64


class ImportData(models.TransientModel):
    _name = 'import.data'


    def _get_outputs(self):
        if self._context.get('default_product_out'):
            return self.env['hydrofarm.outputs'].search([('id', 'in',self._context.get('default_product_out'))])


    fetched_ids = fields.Many2many('hydrofarm.outputs',
                                   'hydrofarm_group_rel', string="OutPut", default=lambda self: self._get_outputs(),
                                   required=True)

    def import_data(self):
        products_view = self.env['product.product']
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
                req = requests.post(request_url, data=data, headers=headers, timeout=1000)
                print(req)
                req.raise_for_status()
                parents_dict = req.json()
                access_token = parents_dict.get('access_token')
                url = hydrofarm.url + "/api/products/getProducts"
                req_headers = {
                    'Content-Type': "application/json",
                    'Authorization': "Bearer " + access_token,
                }
                request_data = {
                    "keyword": prd.sku,
                    "includeProductVariants": True
                }
                data = json.dumps(request_data)
                req = requests.post(url, data=data, headers=req_headers, timeout=1000)
                print(req.text)
                req.raise_for_status()

                products_dict = req.json()[0]

                vendor = self.env['res.partner'].search([('name', '=', hydrofarm.partner.name), ('is_api_vendor', '=', True)])
                if vendor:
                    vendor_mapping = self.env['vendor.mapping'].search([('vendor', '=', vendor.id)])
                    if vendor_mapping:
                        for mapping in vendor_mapping:
                            mapping_product_name = self.env['vendor.mapping'].search([('vendor', '=', vendor.id),('vendor_api_ref', '=', 'name')],limit=1)
                            product_obj = self.env['product.product'].search([(mapping_product_name.odoo_api_field_ref.name, '=', products_dict.get('name'))])
                            if not product_obj:
                                vendor_mapping1 = self.env['vendor.mapping'].search([('vendor', '=', vendor.id),
                                                                                     ('vendor_api_ref' ,"not in" ,['weight','images']),
                                                                                     ('odoo_api_model_ref.name' ,"not in", ['Supplier Pricelist'])
                                                                                    ])
                                print(vendor_mapping1,'vendor_mapping1')
                                general_my_dict = {}
                                for line1 in vendor_mapping1:
                                    general_my_dict.update({line1.odoo_api_field_ref.name : products_dict.get(line1.vendor_api_ref)})
                                product_obj = self.env['product.product'].sudo().create(general_my_dict)

                                # product_obj = self.env['product.product'].sudo().create({
                                #     mapping_product_name.odoo_api_field_ref.name: products_dict.get('name')
                                # })

                            products_view += product_obj
                            if mapping.odoo_api_model_ref.name == 'Product':
                                if mapping.vendor_api_ref == 'weight':
                                    if products_dict.get('dimensions') and products_dict.get('dimensions')[0]:
                                        product_obj.write({
                                            mapping.odoo_api_field_ref.name: products_dict.get('dimensions')[0].get(
                                                mapping.vendor_api_ref)})
                                if products_dict.get('dimensions') and products_dict.get('dimensions')[0]:
                                    product_obj.write(
                                        {'volume': float(products_dict.get('dimensions')[0].get('height')) *
                                                   float(products_dict.get('dimensions')[0].get('width')) *
                                                   float(products_dict.get('dimensions')[0].get('depth'))})
                                if mapping.vendor_api_ref == 'images':
                                    if products_dict.get('images'):
                                        print(products_dict.get('images'), "image_base64image_base64")
                                        image_base64 = base64.b64encode(
                                            requests.get(
                                                products_dict.get('images')[0].get('url').strip()).content).replace(
                                            b'\n', b'')

                                        product_obj.write(
                                            {mapping.odoo_api_field_ref.name: image_base64})

                                elif products_dict.get(mapping.vendor_api_ref):
                                    product_obj.write({mapping.odoo_api_field_ref.name: products_dict.get(
                                        mapping.vendor_api_ref)})
                            if mapping.odoo_api_model_ref.name == 'Supplier Pricelist':
                                product_exists_supplier = self.env[mapping.odoo_api_model_ref.model].search(
                                    [('name', '=', vendor.id),
                                     ('product_id', '=', product_obj.id)], limit=1)
                                if not product_exists_supplier:
                                    product_exists_supplier = self.env['product.supplierinfo'].create({
                                        'name': vendor.id,
                                        'product_id': product_obj.id,
                                        'product_tmpl_id': product_obj.product_tmpl_id.id
                                    })

                                wholesale_price = products_dict.get('price').get('wholesalePrice')[0]
                                # .get('yourPrice')
                                # wholesale_qtyStart = products_dict.get('price').get('wholesalePrice')[0].get('qtyStart')
                                # dict_whole_sale = {}
                                # dict_whole_sale.update({
                                #     mapping.odoo_api_field_ref.name: wholesale_price.get(mapping.vendor_api_ref),
                                # })
                                # dict_whole_sale.update({
                                #     mapping.odoo_api_field_ref.name: wholesale_price.get(mapping.vendor_api_ref),
                                # })
                                product_exists_supplier.write({
                                    mapping.odoo_api_field_ref.name: wholesale_price.get(mapping.vendor_api_ref),
                                })

                tree_view = self.env.ref('hydrofarm_integration.hydrofarm_outputs_form_view')
            print(products_view.ids)
            return {
                'domain': [('id', 'in', products_view.ids)],
                'name': _('Products'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'product.product',
                'view_id': False,
                'type': 'ir.actions.act_window'
            }

        except requests.HTTPError:
            print("hiiiiiiisdfasfasdfasdfasfasiiiiiiiiiiiii")




class HydroFarmImportData(models.TransientModel):
    _name = 'hydrofarm.outputs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HydroFarm Outputs'


    name = fields.Char(string="Name")
    sku = fields.Char(string="Sku")
    check_box = fields.Boolean(string='Select')
