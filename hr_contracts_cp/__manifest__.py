{
    'name': "Employees Contracts CP - Commprog Version",
    'category': "Employees/Employees",
    'author': "Commprog",
    "license": "AGPL-3",
    'depends': ['hr', 'hr_contract', 'hr_payroll'],
    'data': [
        # security
        "security/ir.model.access.csv",
        # views
        "views/contract_cp.xml",
        # report
        "report/employee_monthly_cost_report.xml",
        # wizard
        "wizard/employee_monthly_cost_wizard.xml",
    ],
    "application": False,
    "installable": True,

}