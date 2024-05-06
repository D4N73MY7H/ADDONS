from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    duns = fields.Char(string='DUNS')
    standard = fields.Text(string='Standards')

