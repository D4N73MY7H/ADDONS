# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

class EsigReport(models.TransientModel):
    _name = "wizard.esig.report"
    _description = "Esig 025 Report"


    def _default_date_start(self):
        date_start=time.strftime('%Y-%m-01')
        print("DATE START",date_start)
        return date_start


    def _default_date_end(self):
        date_start=time.strftime('%Y-%m-01')
        start_time=datetime.strptime(date_start, '%Y-%m-%d')
        print("START TIME",start_time)
        end_time =start_time + relativedelta(months=1,days=-1)
        date_end=str(end_time)
        print("DATE END",date_end)
        return date_end

    department_id = fields.Many2one('hr.department',string='Department')
    start_date = fields.Date('Start Date', default=_default_date_start)
    end_date = fields.Date('End Date', default=_default_date_end)
    employee_id=fields.Many2one('hr.employee','Employee')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id=False

    @api.onchange('department_id')
    def onchange_department_id(self):
        if self.department_id:
            self.employee_id=False


    def employee_esig_report(self):
        self.ensure_one()
        [data] = self.read()
        print(data)
        # filters==>
        department = data['department_id']
        start_date = data['start_date']
        end_date = data['end_date']
        employee_id = data['employee_id']


        filter = []
        filter.append(('state', 'in', ('confirm', 'done')))
        if start_date:
            filter.append(('date_from', '>=', start_date))
        if end_date:
            filter.append(('date_to', '<=', end_date))
        if employee_id:
            filter.append(('employee_id', '=', employee_id[0]))
        if department:
            filter.append(('department_id', '=', department[0]))
        payment = self.env['hr.payslip'].search(filter, order="employee_id asc")
        datas = {
            'ids': payment.ids,
            'model': 'hr.payslip',
            'form': data
        }
        print(filter, "Filtri")
        print("DATAT",datas)
        return self.env.ref('cp_payroll.action_esig').report_action(payment, data=datas)

    @api.onchange('start_date')
    def onchange_start_date(self):
        if not self.start_date:
            return {}
        if self.start_date.day != 1:
            warning = {
                'title': _('Input Date Warning!'),
                'message': _('Start date of the report must be the first day of a month')
            }
            return {'warning': warning}
        else:
            start_time = datetime.strptime(str(self.start_date), '%Y-%m-%d')
            end_time = start_time + relativedelta(months=1, days=-1)
            date_end = str(end_time.date())
            self.end_date = date_end
