from collections import defaultdict
from markupsafe import Markup
from odoo import models, fields, api, Command, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, plaintext2html
from odoo.addons import decimal_precision as dp


class CPHrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'
    _description = 'Salary Rule Input'

    type_id = fields.Many2one(
        'hr.payroll.structure.type', required=False)
    max_wage = fields.Float('Maximum Wage')
    min_wage = fields.Float('Minimum Wage')
    avarage_days = fields.Integer('Avarage Days')



class CPHrPayslip(models.Model):
    _inherit = 'hr.payslip'

    net_residual = fields.Float('Net residual', compute='_net_residual', digits=dp.get_precision('Payroll'))
    net_total = fields.Float('Net total', compute='_net_total', digits=dp.get_precision('Payroll'))

    @api.depends('line_ids')
    def _net_total(self):
        net_total = 0.0
        for line in self.line_ids:
            if line.code == 'NET':
                net_total = line.total
        self.net_total = net_total


    @api.depends('line_ids')
    def _net_residual(self):
        payslip_payment = self.env['hr.payslip.payment']
        payslip_payment_line = self.env['payslip.payment.line']
        for payslip in self:
            net_total = 0.0
            amount_payed = 0.0

            for line in payslip.line_ids:
                if line.code=='NET':
                    net_total = line.total
                    break

            #Marrim linjat lidhur me payslipin dhe payslip run id
            payslip_payment_line_ids = payslip_payment_line.search([
                ('payslip_payment_id.payslip_run_id', '=', payslip.payslip_run_id.id),
                ('payslip_payment_id.state', '=', 'done'),
                ('payslip_id', '=', payslip.id)
            ])

            amount_payed = sum(payment_line.payment_amount for payment_line in payslip_payment_line_ids)

            #Llogaritet net_residual per cdo payslip vecmas
            net_residual = net_total - amount_payed
            #Llogaritet net_total per cdo payslip
            payslip.net_total = net_total
            payslip.net_residual = net_residual


    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to', 'struct_id')
    def _compute_input_line_ids(self):
        '''
        Shtimi i linjave(other input types) ne payslip.
        '''
        contracts = self.env['hr.contract'].search_read([('id', 'in', self.contract_id.ids)])
        input_types = self.env['hr.payroll.structure'].search_read([('id', 'in', self.struct_id.ids)],fields=['input_line_type_ids'])

        for contract in contracts:
            input_line_vals = []

            #find the input types if they exist on payslip
            input_line_codes=[line.code for line in self.input_line_ids]

            for input_type in input_types:
                #retrieve id from input_types
                input_type_ids = input_type.get('input_line_type_ids', [])
                input_codes = self.env['hr.payslip.input.type'].search_read([('id', 'in', input_type_ids)])

                # add input lines based on conditions
                for input_code in input_codes:
                    if input_code['code'] not in input_line_codes:
                        input_line_vals.append(Command.create({
                            'name': input_code['name'],
                            'code': input_code['code'],
                            'input_type_id': input_code['id'],
                            'contract_id': contract['id']
                        }))

            self.update({'input_line_ids': input_line_vals})



















