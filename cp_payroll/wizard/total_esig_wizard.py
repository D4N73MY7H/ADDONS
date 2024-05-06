# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from odoo import api, fields, models, _

class EsigTotalReport(models.TransientModel):
    _name = "wizard.esig_total.report"
    _description = "Esig 025 total Report"


    def _default_date_start(self):
        date_start=time.strftime('%Y-01-01')
        return date_start
    def _default_date_end(self):
        return time.strftime('%Y-12-31')

    start_date = fields.Date('Start Date', default=_default_date_start, required=True)
    end_date = fields.Date('End Date', default=_default_date_end, required=True)


    def employee_esig_report(self):
        self.ensure_one()
        [data] = self.read()
        start_date = data['start_date']
        end_date = data['end_date']
        filter = []
        if start_date:
            filter.append(('date_from', '>=', start_date))
        if end_date:
            filter.append(('date_from', '<=', end_date))
        payment = self.env['hr.payslip'].search(filter)
        datas = {
            'ids': payment.ids,
            'model': 'hr.payslip',
            'form': data
        }
        return self.env.ref('cp_payroll.action_esig_total').report_action(payment, data=datas)