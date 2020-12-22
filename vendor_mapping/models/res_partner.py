from odoo import models,fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_api_vendor = fields.Boolean("API Vendor")
