# -*- coding: utf-8 -*-

import calendar
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date


class WageStructureReport(models.AbstractModel):
    _name = 'report.hr_cp.wage_structure_report'

    def get_lines(self, data):
        months = {'01': 'Janar', '02': 'Shkurt', '03': 'Mars', '04': 'Prill', '05': 'Maj',
                  '06': 'Qershor', '07': 'Korrik', '08': 'Gusht', '09': 'Shtator', '10': 'Tetor',
                  '11': 'Nëntor', '12': 'Dhjetor'}
        lines = []
        year = data['form']['year']
        month = data['form']['month']
        employee_ids = data['employee_ids']
        employees = self.env['hr.employee'].browse(employee_ids)
        if month:
            start_date = '%s-%s-01' % (year, month)
            print(start_date,"START DATE")
            end_date = str(datetime.strptime(start_date, '%Y-%m-%d') + relativedelta(months=1, day=1, days=-1))
            print(end_date,"END DATE")
            payslip_ids = self.env['hr.payslip'].search([('state', 'not in', ('verify', 'cancel','draft',)), ('date_from', '=', start_date), ('date_to', '=', end_date), ('employee_id', 'in', employees.ids)])
            if employees:
                for employee in employees:
                    lines_payslip = []
                    tot_bruto = tot_net = tot_bonus = tot_cost = tot_hourly_cost = tot_net_profit = tot_monthly_bonus = 0
                    index = 0
                    emp_payslip_ids = payslip_ids.filtered(lambda e: e.employee_id.id == employee.id)
                    if emp_payslip_ids:
                        for payslip in emp_payslip_ids:
                            paga_bruto = payslip.line_ids.filtered(lambda l: l.category_id.code == 'GROSS')[0].total or 0.0
                            paga_neto = payslip.line_ids.filtered(lambda l: l.category_id.code == 'NET')[0].total or 0.0
                            bonusi =  payslip.contract_id.bonus if  payslip.contract_id.bonus else 0.0
                            kosto_totale = (sum(emp_payslip_ids[0].line_ids.filtered(lambda l: l.category_id.code == 'GROSS' or l.category_id.code == 'COMP').mapped('total')) or 0.0) + bonusi
                            kosto_orare = kosto_totale / payslip.contract_id.nr_mesatar_oreve

                            monthly_bonus = sum(self.env['annual.bonus'].search([('employee_id', '=', employee.id), ('year', '=', year), ('month', '=', month)]).mapped('value'))
                            tot_bruto += paga_bruto
                            tot_net += paga_neto
                            tot_bonus += monthly_bonus
                            tot_net_profit += tot_net + monthly_bonus
                            tot_cost += kosto_totale
                            tot_hourly_cost += kosto_orare
                            tot_monthly_bonus += monthly_bonus
                            index += 1
                            employee_payslip = {
                                'index': index,
                                'month': months.get(month),
                                'paga_bruto': '{0:,.2f}'.format(float(paga_bruto)),
                                'paga_neto': '{0:,.2f}'.format(float(paga_neto)),
                                'bonus': '{0:,.2f}'.format(float(monthly_bonus)),
                                'neto_profit': '{0:,.2f}'.format(float(tot_net_profit)),
                                'total_cost': '{0:,.2f}'.format(float(kosto_totale)),
                                'hourly_cost': '{0:,.2f}'.format(float(kosto_orare)),
                                'monthly_bonus': '{0:,.2f}'.format(float(monthly_bonus)),
                            }
                            lines_payslip.append(employee_payslip)

                    if lines_payslip:
                        vals = {
                            'employee': employee.name or False,
                            'department': employee.department_id.name or False,
                            'payslips': lines_payslip,
                            'tot_bruto': '{0:,.2f}'.format(float(tot_bruto)),
                            'tot_net': '{0:,.2f}'.format(float(tot_net)),
                            'tot_bonus': '{0:,.2f}'.format(float(tot_bonus)),
                            'tot_net_profit': '{0:,.2f}'.format(float(tot_net_profit)),
                            'tot_cost': '{0:,.2f}'.format(float(tot_cost)),
                            'tot_hourly_cost': '{0:,.2f}'.format(float(tot_hourly_cost)),
                            'tot_monthly_bonus': '{0:,.2f}'.format(float(tot_monthly_bonus)),
                        }
                        lines.append(vals)

        else:
            payslip_ids = self.env['hr.payslip'].search([
                ('state', 'not in', ('verify', 'cancel','draft')),
                ('employee_id', 'in', employees.ids)
            ]).filtered(lambda x: x.date_from.strftime('%Y') == year)
            if employees:
                for employee in employees:
                    lines_payslip = []
                    tot_bruto = tot_net = tot_bonus = tot_cost = tot_hourly_cost = tot_net_profit = tot_monthly_bonus = 0
                    index = 0
                    for m in months:
                        monthly_bonus = sum(self.env['annual.bonus'].search([('employee_id', '=', employee.id), ('year', '=', year), ('month', '=', month)]).mapped('value'))
                        index += 1
                        emp_payslip_ids = payslip_ids.filtered(lambda e: e.employee_id.id == employee.id and months.get(e.date_from.strftime('%m')) == months.get(m))
                        if emp_payslip_ids:
                            for payslip in emp_payslip_ids:
                                paga_bruto = payslip.line_ids.filtered(lambda l: l.category_id.code == 'GROSS')[0].total if payslip.line_ids.filtered(
                                    lambda l: l.category_id.code == 'GROSS') else 0.0
                                paga_neto = payslip.line_ids.filtered(lambda l: l.category_id.code == 'NET')[0].total if payslip.line_ids.filtered(
                                    lambda l: l.category_id.code == 'NET') else 0.0
                                bonusi =  payslip.contract_id.bonus if  payslip.contract_id.bonus else 0.0
                                kosto_totale = (sum(payslip.line_ids.filtered(lambda l: l.category_id.code == 'GROSS' or l.category_id.code == 'COMP').mapped('total')) or 0.0) + bonusi
                                kosto_orare = kosto_totale / payslip.contract_id.nr_mesatar_oreve

                                tot_bruto += paga_bruto
                                tot_net += paga_neto
                                tot_bonus += monthly_bonus
                                tot_net_profit += paga_neto + monthly_bonus
                                tot_cost += kosto_totale
                                tot_hourly_cost += kosto_orare
                                tot_monthly_bonus += monthly_bonus

                                employee_payslip = {
                                    'index': index,
                                    'month': months.get(m),
                                    'paga_bruto': '{0:,.2f}'.format(float(paga_bruto)),
                                    'paga_neto': '{0:,.2f}'.format(float(paga_neto)),
                                    'bonus': '{0:,.2f}'.format(float(monthly_bonus)),
                                    'neto_profit': '{0:,.2f}'.format(float(tot_net_profit)),
                                    'total_cost': '{0:,.2f}'.format(float(kosto_totale)),
                                    'hourly_cost': '{0:,.2f}'.format(float(kosto_orare)),
                                    'monthly_bonus': '{0:,.2f}'.format(
                                        float(monthly_bonus)) if monthly_bonus != 0 else '',
                                }
                                lines_payslip.append(employee_payslip)


                        else:
                            tot_monthly_bonus += monthly_bonus
                            employee_payslip = {
                                            'index': index,
                                            'month': months.get(m),
                                            'paga_bruto': '',
                                            'paga_neto': '',
                                            'bonus': '',
                                            'neto_profit': '',
                                            'total_cost': '',
                                            'hourly_cost': '',
                                            'monthly_bonus': '{0:,.2f}'.format(float(monthly_bonus)) if monthly_bonus != 0 else '',
                            }
                            lines_payslip.append(employee_payslip)

                    vals = {
                        'employee': employee.name or False,
                        'department': employee.department_id.name or False,
                        'payslips': lines_payslip,
                        'tot_bruto': '{0:,.2f}'.format(float(tot_bruto)),
                        'tot_net': '{0:,.2f}'.format(float(tot_net)),
                        'tot_bonus': '{0:,.2f}'.format(float(tot_bonus)),
                        'tot_net_profit': '{0:,.2f}'.format(float(tot_net_profit)),
                        'tot_cost': '{0:,.2f}'.format(float(tot_cost)),
                        'tot_hourly_cost': '{0:,.2f}'.format(float(tot_hourly_cost)),
                        'tot_monthly_bonus': '{0:,.2f}'.format(float(tot_monthly_bonus)),
                    }
                    if lines_payslip:
                        lines.append(vals)
        return lines

    @api.model
    def _get_report_values(self, docids, data=None):
        wage_structure_report = self.env['ir.actions.report']._get_report_from_name('hr_cp.wage_structure_report')
        payslip_ids = self.env['hr.payslip'].browse(self.ids)
        datas = {
            'doc_ids': self.ids,
            'doc_model': wage_structure_report.model,
            'docs': payslip_ids,
            'get_lines': self.get_lines(data),
        }
        print(datas,"DATAT")
        return datas