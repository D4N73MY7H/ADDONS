# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime


class WageHistoryReport(models.TransientModel):
    _name = "wizard.wage.history"
    _description = "Wage History Report"

    employee_id = fields.Many2one('hr.employee', string='Employee')


    def print_wage_report(self):
        self.ensure_one()
        [data] = self.read()
        data = {
            'model': 'wizard.wage.history',
            'form': data,
        }
        print(data)
        return self.env.ref('hr_cp.action_wage_history').report_action(self,data=data)