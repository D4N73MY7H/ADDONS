# -*- coding: utf-8 -*-
{
    'name': "Payroll - Commprog Version",
    'category': "Payroll/Payroll",
    'author': "Commprog",
    "license": "AGPL-3",
    'depends': ['hr', 'hr_payroll', 'hr_payroll_account', 'hr_holidays', 'hr_contract', 'base'],
    'data': [
        "security/ir.model.access.csv",
        'data/hr_payroll_data.xml',
        'views/cp_hr_payroll.xml',
        'views/cp_time_off.xml',
        'views/cp_payroll.xml',
        'reports/report_esig.xml',
        'reports/report_esig_total.xml',
        'wizard/esig_wizard_view.xml',
        'wizard/total_esig_wizard_view.xml',
    ],
    "application": False,
    "installable": True,
    'license': 'LGPL-3',
}



