from odoo import models, fields, api, Command, _
import time
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    payslip_payment_id = fields.Many2one(comodel_name='hr.payslip.payment', string='Payslip_payment_id', required=False) #per pagesen e pagave
    payslip_id = fields.Many2one('hr.payslip', 'Payslip', required=True) #per pagesen e pagave
    fiscal_closure_id = fields.Many2one('fiscal.year.closure', string='Fical Year Closure', )  # per fiscal year closure