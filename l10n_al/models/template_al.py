# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('al')
    def _get_sq_template_data(self):
        return {
            'property_account_receivable_id': '411',
            'property_account_payable_id': '401',
            'property_account_expense_categ_id': '608',
            'property_account_income_categ_id': '7088',
            'property_tax_payable_account_id': '4457',
            'property_tax_receivable_account_id': '4456',
            'code_digits': '0',
        }

    @template('al', 'res.company')
    def _get_sq_res_company(self):
        return {
            self.env.company.id: {
                'account_fiscal_country_id': 'base.al',
                'bank_account_code_prefix': '5121',
                'cash_account_code_prefix': '5311',
                'transfer_account_code_prefix': '581',
                'income_currency_exchange_account_id': '769',
                'expense_currency_exchange_account_id': '669',
            },
        }