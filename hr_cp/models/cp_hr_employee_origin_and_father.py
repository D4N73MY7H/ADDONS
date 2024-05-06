from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class Employee(models.Model):
    _inherit = "hr.employee"

    father_name = fields.Char(string="Father's Name")
    employee_origin_id = fields.Many2one('employee.origin', 'Employee Origin')
    employee_measures = fields.One2many('masat.disiplinore', 'employee_id', string='Disciplinary Measures')
    annual_bonus_ids = fields.One2many('annual.bonus', 'employee_id', string="Annual Bonus")
