# -*- coding: utf-8 -*-
{
    "name": "Customs - Commprog Version",
    "category": "Accounting/Customs",
    "summary": "Customs module for Accounting",
    "author": "Commprog",
    "license": "AGPL-3",
    "depends": ['account_accountant', 'stock', 'stock_landed_costs'],
    "application": False,
    "installable": True,
    "data": [
        'views/customs_menu.xml',
        'views/template.xml',
        'security/customs_security.xml',
        'security/ir.model.access.csv'
    ],
}
