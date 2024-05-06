# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime

months = [
    'Janar',
    'Shkurt',
    'Mars',
    'Prill',
    'Maji',
    'Qeshor',
    'Korrik',
    'Gusht',
    'Shtator',
    'Tetor',
    'Nentor',
    'Dhjetor',
]


class PayslipRunGender(models.AbstractModel):
    _name = 'report.cp_payroll.report_esig_total'

    def last_day_of_month(self, any_day):
        next_month = any_day.replace(day=28) + datetime.timedelta(days=4) #llogarisim dhe per shkurtin
        return  next_month - datetime.timedelta(days=next_month.day)

    def get_data(self,payslip_ids):
        gross = ewsi = ewhc = esiit = ehc = paga_tap = ndalesa = net = eit = bkb = bhi = 0
        for payslip_id in payslip_ids:
            if payslip_id.line_ids:
                bhi = 0
                for line in payslip_id.line_ids:
                    if line.code == 'EWSI':
                        ewsi = line.total
                    elif line.code == 'EESI':
                        ewsi = line.total
                    elif line.code == 'GROSS':
                        gross = line.total
                    elif line.code == 'BKB':
                        bkb = line.total
                    elif line.code == 'BKG':
                        bkb = line.total
                    elif line.code == 'ESI':
                        esiit = line.total
                    elif line.code == 'EHC':
                        ehc = line.total
                    elif line.code == 'WTB':
                        paga_tap = line.total
                    elif line.code == 'NET':
                        net = line.total
                    elif line.code == 'EWHC':
                        ewhc = line.total
                    elif line.code == 'EIT':
                        eit = line.total
                    elif line.code == 'PD':
                        eit = line.total
                    elif line.code == 'NDTJE':
                        ndalesa = line.total
                    elif line.code == 'BHI':
                        bhi = line.total
                if bhi == 0:
                    bhi = gross
            min_wage = payslip_id.struct_id.min_wage if payslip_id.struct_id.min_wage else 0
        return {
            'gross': gross,
            'ewsi': ewsi,
            'ewhc': ewhc,
            'esiit': esiit,
            'ehc': ehc,
            'tap': paga_tap,
            'ndalesa': ndalesa,
            'net': net,
            'eit': eit,
            'bkb': bkb,
            'bhi': bhi,
            'min_wage': min_wage,
        }

    def get_lines(self, data):
        lines = []
        global months
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        payslip_obj = self.env['hr.payslip']
        year = datetime.datetime.strptime(str(start_date), '%Y-%m-%d').year
        start_month = datetime.datetime.strptime(str(start_date), '%Y-%m-%d').month
        end_month = datetime.datetime.strptime(str(end_date), '%Y-%m-%d').month
        for month in range(start_month, end_month + 1):
            print(month)
            print(months[month - 1])
            filter = []
            filter.append(('state','in',('done','paid')))
            gross = ewsi = ewhc = esiit = ehc = net = eit = bkb = tap = bhi = 0
            last_day = self.last_day_of_month(datetime.date(year,month,1))
            if month < 10:
                first_day = str(year) + '-0' + str(month) + '-' + '01'
            else:
                first_day = str(year) + '-' + str(month) + '-' + '01'

            filter.append(('date_from', '=', first_day))
            filter.append(('date_to', '=', last_day))
            ids = payslip_obj.search(filter)
            nr_employee = 0
            if ids:
                for payslip_id in ids:
                    nr_employee += 1
                    get_data = self.get_data(payslip_id)

                    if get_data['bhi'] and get_data['min_wage']:
                        if get_data['bhi'] <= get_data['min_wage']:
                            get_data['bhi'] = get_data['min_wage']

                    gross += get_data['gross']
                    bkb += get_data['bkb']
                    esiit += get_data['esiit']
                    ewsi += get_data['ewsi']
                    ehc += get_data['ehc']
                    ewhc += get_data['ewhc']
                    bhi += get_data['bhi']
                    tap += get_data['tap']
                    net += get_data['net']
                    eit += get_data['eit']
            vals = {
                'id': month,
                'name': months[month - 1],
                'gross': gross or 0,
                'bkb': bkb or 0,
                'esiit': esiit or 0,
                'ewsi': ewsi or 0,
                'ehc': ehc or 0,
                'ewhc': ewhc or 0,
                'tot_shoqerore': esiit + ewsi or 0,
                'bhi': bhi or 0,
                'tot_shendensore': ewhc + ehc or 0,
                'tap': eit or 0,
                'nr_employee': nr_employee or 0,
            }
            lines.append(vals)

        return lines

    def get_payslip_run(self, data):
        lines = []
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        filter = []
        if start_date:
            filter.append(('date_start', '>=', start_date))
        if end_date:
            filter.append(('date_end', '<=', end_date))
        payslip_obj = self.env['hr.payslip.run'].search(filter)

        for payslip_run_id in payslip_obj:
            vals = {
                'id': payslip_run_id.id,
                'name': payslip_run_id.name
            }
            lines.append(vals)
        return lines


    def get_header(self, data):
        lines = []
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        company = self.env.company
        for company_id in company:
            vals = {
                'vat': company_id.vat or "_______________",
                'name': company_id.name or "_______________",
                'start_date': datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime(
                    '%d/%m/%Y') or "_______________",
                'end_date': datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y') or "_______________",
                'employer_name': company_id.employer_name or "_______________",
                'street': company_id.street or "_______________",
                'viti': start_date[0:4] or "____",
            }
            lines.append(vals)
        return lines

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        dep_cost_report = self.env['ir.actions.report']._get_report_from_name('cp_payroll.report_esig_total')
        dep_ids = self.env['hr.payslip'].browse(self.ids)
        test = {
            'doc_ids': self.ids,
            'doc_model': dep_cost_report.model,
            'docs': dep_ids,
            'get_lines': self.get_lines(data),
            'get_payslip_run': self.get_payslip_run(data),
            'get_header': self.get_header(data),
        }
        print(test)
        return test