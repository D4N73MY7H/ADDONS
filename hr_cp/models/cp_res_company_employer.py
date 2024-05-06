from odoo import models, fields, api


class ResCompanyInherited(models.Model):
    _inherit = 'res.company'
    _description = 'Company Model inherit'

    employer_name = fields.Char(string='Employer Name')
    company_start_date = fields.Date(string='Company Start Date')
