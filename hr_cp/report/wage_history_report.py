# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from datetime import timedelta,datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WageHistoryCosts(models.AbstractModel):
    _name = 'report.hr_cp.wage_history_report'

    def get_lines(self, data):
        employee_id = data['form']['employee_id']
        employee_id = self.env['hr.employee'].browse(employee_id[0])
        contract_lines = []
        lines = []
        tot_paga = tot_diff_value = tot_diff_percent = tot_bonus = tot_net = monthly_bonus = 0
        nr_rendor = 0
        contract_ids = self.env['hr.contract'].search([('employee_id', '=', employee_id.id)], order='date_start desc')
        print(employee_id.name, "Emri punonjesit")
        if contract_ids:
            for contract in contract_ids:
                period_bonus = 0
                last_wage = contract.contract_id_last.wage if contract.contract_id_last else 0.0
                tot_paga += contract.wage
                tot_diff_value += (contract.wage - last_wage) if contract.contract_id_last else 0.0
                tot_diff_percent += ((contract.wage - last_wage) / last_wage) * 100 if last_wage != 0 else 0.0
                change_date = contract.date_start
                annual_bonuses = self.env['annual.bonus'].search([('employee_id', '=', employee_id.id)])
                tot_net += contract.net
                monthly_bonus += contract.bonus if contract.bonus else 0.0

                if annual_bonuses:
                    period_bonus = sum(annual_bonuses.filtered(
                        lambda x: (datetime(int(x.year), int(x.month), 1)) >= datetime.strptime(
                            contract.date_start.strftime('%Y-%m-%d'), '%Y-%m-%d')
                                  and ((datetime(int(x.year), int(x.month), 1)) <= datetime.strptime(
                            contract.date_end.strftime('%Y-%m-%d'), '%Y-%m-%d') if contract.date_end else True)).mapped(
                        'value'))

                    tot_bonus += period_bonus

                nr_rendor += 1
                emp_contract = {
                    'nr_rendor': nr_rendor,
                    'description': contract.name or False,
                    'period': '%s - %s' % (datetime.strptime(str(contract.date_start), '%Y-%m-%d').strftime('%d/%m/%Y'),
                                           datetime.strptime(str(contract.date_end), '%Y-%m-%d').strftime(
                                               '%d/%m/%Y') if contract.date_end else ''),
                    'net': contract.net,
                    'bonus': period_bonus,
                    'paga': contract.wage,
                    'period_bonus': '{0:,.2f}'.format(float(period_bonus)) if period_bonus != 0 else '',
                    'change_date': datetime.strptime(change_date.strftime('%Y-%m-%d'), '%Y-%m-%d').strftime('%d/%m/%Y'),
                    'diff_value': (contract.wage - last_wage) if contract.contract_id_last else 0.0,
                    'diff_percent': '{0:,.2f}'.format(
                        float(((contract.wage - last_wage) / last_wage) * 100 if last_wage != 0 else 0.0)),

                }
                contract_lines.append(emp_contract)
            vals = {
                'employee': employee_id.name,
                'department': employee_id.department_id.name,
                'contracts': contract_lines,
                'tot_paga': tot_paga,
                'tot_net': '{0:,.2f}'.format(float(tot_net)) if tot_net != 0 else '',
                'monthly_bonus': '{0:,.2f}'.format(float(monthly_bonus)) if monthly_bonus != 0 else '',
                'tot_diff_value': tot_diff_value,
                'tot_diff_percent': '{0:,.2f}'.format(float(tot_diff_percent)),
                'total_bonus': '{0:,.2f}'.format(float(tot_bonus)) if tot_bonus != 0 else ''}
            lines.append(vals)
            return lines



    def _get_report_values(self, docids, data=None):
        wage_report = self.env['ir.actions.report']._get_report_from_name('hr_cp.report_wage_history')
        contract = self.env['hr.contract'].browse(self.ids)
        datas= {
            'doc_ids': self.ids,
            'doc_model': wage_report.model,
            'docs': contract,
            'get_lines': self.get_lines(data),
        }
        return datas