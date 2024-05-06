# -*- coding: utf-8 -*-
{
    "name": "CRM - Commprog Version",
    "category": "Sales/CRM",
    "summary": "Advanced features for CRM",
    "author": "Commprog",
    "license": "AGPL-3",
    "depends": ['crm', 'helpdesk_cp', 'crm_helpdesk', 'hr', 'hr_timesheet', 'project_enterprise', 'project_cp', 'sale', 'mail', 'board', 'project_timesheet_forecast_sale'],
    "application": False,
    "installable": True,
    "data": [
        # Security
        'security/security_view.xml',
        'security/ir.model.access.csv',

        "views/template.xml",

        # Company contracts view data
        'views/company_contract_view.xml',
        'views/contract_coniguration_view.xml',
        'views/contract_object_view.xml',
        # 'views/contract_component_view.xml',
        'views/sale_order_inherited_view.xml',
        # 'views/crm_stage_inherit.xml',
        'views/cp_project_inherited_view.xml',
        'views/cp_helpdesk_sla_inherited_view.xml',
        'views/cron_data_cp.xml',
        'views/company_contract_state.xml',
        'reports/contract_report_tree_view.xml',
        'reports/contract_report_template_view.xml',
    ],
}
