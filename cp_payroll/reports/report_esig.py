# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PayslipRunGender(models.AbstractModel):
    _name = 'report.cp_payroll.report_esig'

    def get_data(self, payslip_ids):
        gross = ewsi = ewhc = esiit = ehc = paga_tap = ndalesa = net = eit = dite_pune = dite_papunuar = bkb = bhi = 0

        for payslip_id in payslip_ids:
            if payslip_id.worked_days_line_ids:
                for work in payslip_id.worked_days_line_ids:
                    if work.code == 'WORK100':
                        dite_pune = work.number_of_days
                    else:
                        dite_papunuar = work.number_of_days

            if payslip_id.line_ids:
                result_emp = 0.0
                result_bruto = 0.0
                bhi = 0

                for line in payslip_id.line_ids:
                    if line.code == 'EWSI':
                        ewsi = line.total
                    elif line.code =='EESI':
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
            'bkb': bkb,
            'ewsi': ewsi,
            'ewhc': ewhc,
            'esiit': esiit,
            'ehc': ehc,
            'tap': paga_tap,
            'ndalesa': ndalesa,
            'net': net,
            'eit': eit,
            'dite_papunuar': dite_papunuar,
            'dite_pune': dite_pune,
            'bhi': bhi,
            'min_wage': min_wage,
        }

    def get_lines(self,data):
        ids = data['ids']
        lines = []
        payslip_obj = self.env['hr.payslip'].browse(ids)
        if payslip_obj:
            nr_rendor = 0
            for payslip_id in payslip_obj:
                nr_rendor += 1

                # get data from payslips
                get_data = self.get_data(payslip_id)

                # nese paga bruto <= paga min  ather bhi=paga_min perndryshe bhi=paga_bruto(kol24)
                if get_data['bhi'] and get_data['min_wage']:
                    if get_data['bhi'] <= get_data['min_wage']:
                        get_data['bhi'] = get_data['min_wage']


                vals = {
                    'id': nr_rendor,
                    'name': payslip_id.employee_id.name or False,
                    'ssnid': payslip_id.employee_id.ssnid or False,
                    'job_id': payslip_id.employee_id.job_id.name or False,
                    'gross': get_data['gross'] or 0,
                    'bkb': get_data['bkb'] or 0,
                    'ewsi': get_data['ewsi'] or 0,
                    'ewhc': get_data['ewhc'] or 0,
                    'esiit': get_data['esiit'] or 0,
                    'ehc': get_data['ehc'] or 0,
                    'tot_employee': get_data['ehc'] + get_data['ewhc'] or 0,
                    'tot_employeer': get_data['esiit'] + get_data['ewsi'] or 0,
                    'tot_sigurime': get_data['ewsi'] + get_data['esiit'] or 0,
                    'paga_tap': get_data['tap'] or 0,
                    'tap': get_data['eit'] or 0,
                    'tot_shendensore': get_data['ewhc'] + get_data['ehc'] or 0,
                    'ndalesa': get_data['ndalesa'] or 0,
                    'net': get_data['net'] or 0,
                    'dite_pune': get_data['dite_pune'] or 0,
                    'dite_papunuar': get_data['dite_papunuar'] or 0,
                    'bhi': get_data['bhi'] or 0,
                }
                lines.append(vals)
        else:
             raise UserError(_("Nuk ka te dhena"))
        print(lines, "LINJAT PER GET LINES")
        return lines

    def get_payslip_run(self, data):
        ids = []
        lines = []
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        payslip_obj = self.env['hr.payslip.run']
        filter = []
        if start_date:
            filter.append(('date_start', '>=', start_date))
        if end_date:
            filter.append(('date_end', '<=', end_date))

        payslip_run = payslip_obj.search(filter)

        for payslip_run_id in payslip_run:
            vals={
                'id':payslip_run_id.id,
                'name':payslip_run_id.name
            }
            lines.append(vals)
        print(lines, "LINJAT PER PAYSLIP RUN")
        return lines

    def get_headers(self,data):
        lines = []
        start_date = data['form']['start_date']
        company_id = self.env.company

        for company in company_id:
            vals = {
                'vat': company.vat or "_______________",
                'employer_name': company_id.employer_name or "_______________",
                'street': company_id.street or "_______________",
                'viti': start_date[0:4] or "____",
                'month': start_date[5:7] or "__",
            }
            lines.append(vals)
        return lines

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        dep_cost_report = self.env['ir.actions.report']._get_report_from_name('cp_payroll.report_esig')
        dep_ids = self.env['hr.payslip'].browse(self.ids)
        test = {
            'doc_ids': self.ids,
            'doc_model': dep_cost_report.model,
            'docs': dep_ids,
            'get_lines': self.get_lines(data),
            'get_payslip_run': self.get_payslip_run(data),
            'get_header': self.get_headers(data),
        }
        return test






