from datetime import datetime, date
from odoo import models, fields, _, api


class HRContractCP(models.Model):
    _inherit = "hr.contract"


    contract_id_last = fields.Many2one('hr.contract', string="Last Contract")
    bonus = fields.Monetary('Bonus mujor neto' )


class Annual_Bonus(models.Model):
    _name = "annual.bonus"
    _description = "Annual Bonus"

    month = fields.Selection([('01', 'January'),
                              ('02', 'February'),
                              ('03', 'March'),
                              ('04', 'April'),
                              ('05', 'May'),
                              ('06', 'June'),
                              ('07', 'July'),
                              ('08', 'August'),
                              ('09', 'September'),
                              ('10', 'October'),
                              ('11', 'November'),
                              ('12', 'December')], required=True, string='Muaji')
    year = fields.Char(size=4, required=True, string='Viti')
    value = fields.Float(string='Vlera Neto')
    value_gross = fields.Float(string='Vlera Bruto')
    description = fields.Char(string='Shenime')
    employee_id = fields.Many2one('hr.employee', string='Employee')
