from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class EmployeeOrigin(models.Model):
    _name = "employee.origin"
    _description = "Employee origin"

    name = fields.Char(string='Education origin')
    active = fields.Boolean(string='Active', default=True)
