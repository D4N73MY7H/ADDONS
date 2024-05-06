from odoo import api, fields, models, _
import time
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta


class WageStructureWizard(models.TransientModel):
    _name = "wizard.wage_structure.report"
    _description = "Raport i struktures se pages"

    def _default_get_year(self):
        today = fields.Date.from_string(fields.Date.context_today(self))
        return today.strftime('%Y')

    def _get_department(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        print(emp_ids,"EMP IDS")
        return emp_ids and emp_ids[0].department_id.id or False


    def _get_department_ids(self):
        lista = []
        def department_tree(id, lista):
            lista.append(id.id)
            result = self.env['hr.department'].search([('parent_id.id', '=', id.id)])
            for res in result:
                department_tree(res, lista)
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        if emp_ids and not self.env.user.has_group('hr.group_hr_manager'):
            department_tree(emp_ids[0].department_id, lista)
            print(lista,"LISTA")
            return lista
        else:
            return self.env['hr.department'].search([]).ids


    year = fields.Char(string='Year', size=4, default=_default_get_year)
    month = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'),
                              ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'),
                              ('11', 'November'), ('12', 'December')], string='Month')
    department_id = fields.Many2one('hr.department', string='Department', default=_get_department)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_ids = fields.Many2many('hr.department', string='Departments', default=_get_department_ids)

    @api.onchange('department_id')
    def _onchange_department_id(self):
        def department_tree(id, lista):
            lista.append(id.id)
            result = self.env['hr.department'].search([('parent_id.id', '=', id.id)])
            for res in result:
                department_tree(res, lista)

        self.employee_id = False
        lista = []
        if self.department_id:
            department_tree(self.department_id, lista)
            ids = self.env['hr.employee'].sudo().search([('department_id', 'in', lista)]).ids
        else:
            ids = self.env['hr.employee'].sudo().search([]).ids
        result = {'domain': {'employee_id': [('id', 'in', ids)]}}
        return result

    def wage_structure_report(self):
        self.ensure_one()
        [data] = self.read()

        def department_tree(id, lista):
            lista.append(id.id)
            result = self.env['hr.department'].search([('parent_id.id', '=', id.id)])
            for res in result:
                department_tree(res, lista)

        dept_id = data['department_id']
        employee_id = data['employee_id']
        employee_ids = []

        if employee_id:
            employee_ids.append(employee_id[0])
        elif dept_id:
            lista = []
            department_tree(self.department_id, lista)
            dept_employees = self.env['hr.employee'].search([('department_id', 'in', lista)])
            employee_ids = dept_employees.ids
        else:
            employee_ids = self.env['hr.employee'].search([]).ids
        datas = {
            'employee_ids': employee_ids,
            'model': 'hr.payslip',
            'form': data
        }
        print(datas)
        return self.env.ref('hr_cp.action_struktura_pages').report_action(employee_ids, data=datas)