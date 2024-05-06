from odoo import models, fields, api


class CompanyContractConfigurationCP(models.Model):
    _name = "cp.company_contract_performance"
    _description = "Company Contract Performance"

    name = fields.Char(string="Name", required=True)
