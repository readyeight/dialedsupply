from odoo import models, fields, api



class VendorMapping(models.Model):
    _name = 'vendor.mapping'

    vendor = fields.Many2one('res.partner', string="Vendor", domain=[('is_api_vendor', '=', True)], required=True)
    vendor_api_ref = fields.Char(string="Vendor API field", required=True)
    odoo_api_model_ref = fields.Many2one('ir.model', string="Odoo Model", required=True)
    odoo_api_field_ref = fields.Many2one('ir.model.fields', string="Odoo Fields",
                                         domain="[('model_id', '=', odoo_api_model_ref)]", required=True)
    # field_type = fields.Selection([('general', 'General'),
    #                                ('attribute', 'Attribute'),
    #                                ('price', 'Price'),
    #                                ('documents', 'Documents'),
    #                                ('related', 'Related'),
    #                                ('image', 'Image')], string='Vendor API field Type', required=True,
    #                          default='general')


    _sql_constraints = [
        ('vendor_api_ref_uniq', 'unique(vendor_api_ref,odoo_api_model_ref,vendor)', 'Vendor API field should be unique!')
    ]