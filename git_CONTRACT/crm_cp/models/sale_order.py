from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    company_contract_id = fields.Many2one(string="Kontrata", comodel_name="cp.company_contract")