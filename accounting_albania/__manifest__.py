{
    "name": "Accounting - Commprog Version",
    "category": "Accounting/Accounting",
    "summary": "Advanced features for Accounting",
    "author": "Commprog",
    "license": "AGPL-3",
    "depends": ['account', 'stock', 'customs_albania','hr_payroll','account_accountant'],
    "installable": True,
    "data": [
        'security/ir.model.access.csv',

        'views/account_move_views.xml',
        'views/payslip_payment.xml',
        'views/cp_employe.xml',
        'views/fiscal_year_closure.xml'

    ],
    'assets': {
        'web.assets_backend': [
            'accounting_albania/static/src/components/**/*',
        ],
    },
}
