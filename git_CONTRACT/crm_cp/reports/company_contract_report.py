from odoo import models, fields, api


class CpCategoriesContractReport(models.AbstractModel):
    _name = 'report.crm_cp.dynamic_report_categories_contract_report'
    _description = 'Categories Contract Report Data'

    @api.model
    def _get_report_values(self, docids, data=None):
        contracts = self.env['cp.company_contract'].browse(docids)
        category_count = {}

        for contract in contracts:
            selected_categories = contract.category_ids

            for category in selected_categories:
                category_count[category.name] = category_count.get(category.name, 0) + 1

        return {
            'doc_ids': docids,
            'docs': contracts,
            'category_count': category_count,
        }


class CpPerformanceContractReport(models.AbstractModel):
    _name = 'report.crm_cp.dynamic_report_performance_contract_report'
    _description = 'Categories Contract Report Data'

    @api.model
    def _get_report_values(self, docids, data=None):

        contracts = self.env['cp.company_contract'].browse(docids)

        performance_count = {}

        for contract in contracts:
            performance = contract.contract_performance_id.name
            performance_count[performance] = performance_count.get(performance, 0) + 1

        return {
            'doc_ids': docids,
            'docs': contracts,
            'performance_count': performance_count,
        }