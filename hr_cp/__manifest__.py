# -*- coding: utf-8 -*-
{
    'name': 'Employees - Commprog Version',
    'category': 'Employees/Employees',
    'author': 'Commprog',
    'license': 'AGPL-3',
    'depends': [
        'hr', 'hr_recruitment', 'fleet', 'timesheet_grid', 'hr_contract', 'hr_holidays', 'account',
        'cp_payroll', 'hr_contracts_cp'
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        # Wizard
        'wizard/employee_wage_certificate_wizard_view.xml',
        'wizard/work_office_statement_wizard_view.xml',
        'wizard/struktura_e_pages_wizard_view.xml',
        'wizard/historiku_i_pages_wizard_view.xml',
        # Views
        'views/cp_res_company_duns_view.xml',
        'views/cp_res_company_employer_view.xml',
        'views/cp_employee_origin_views.xml',
        'views/cp_hr_employee_origin_and_father_view.xml',
        'views/cp_hr_employee_responsible.xml',
        'views/cp_hr_contract.xml',
        'views/cp_masat_disiplinore.xml',
        # Report
        'report/report_employee_wage_certificate.xml',
        'report/report_work_office_statement.xml',
        'report/wage_history_report.xml',
        'report/wage_structure_report.xml',

    ],
    'application': False,
    'installable': True,
}
