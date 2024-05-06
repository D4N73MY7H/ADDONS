from odoo import fields, models, api, _
import datetime
from io import BytesIO
import base64
import xlsxwriter
from odoo.exceptions import ValidationError, AccessError, UserError


def _format_integer(val):
    if val == 0:
        val = '0'
    elif val < 0:
        val = str(abs(val))
        val = ','.join([val[:-3], val[-3:]]) if len(val) > 3 else val
        val = '-' + val
    else:
        val = str(val)
        val = ','.join([val[:-3], val[-3:]]) if len(val) > 3 else val
    return val


class EmployeeMonthlyCost(models.TransientModel):
    _name = 'employee.monthly.cost.wizard'
    _description = 'Employee monthly cost wizard'

    department_id = fields.Many2one('hr.department', string='Department')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    report_type = fields.Selection([('pdf', 'Pdf'), ('xls', 'Excel')], string='Report Type', default='pdf',
                                   required=True)

    def employee_monthly_cost(self):
        self.ensure_one()
        read = self.read()[0]

        department = read.get('department_id')
        employee = read.get('employee_id')
        report_type = read.get('report_type')

        # Get the contract data based on the user field selection
        if department and employee:
            contract_data = self.env['hr.contract'].search_read(
                domain=[
                    ('department_id', '=', department[0]),
                    ('employee_id', '=', employee[0]),
                    ('state', '=', 'open')],
                fields=['wage', 'net', 'sig_shendetesore_punonjesi', 'sig_shoqerore_punonjesi',
                        'sig_shendetesore_punedhenesi', 'sig_shoqerore_punedhenesi', 'tatim_mbi_te_ardhurat',
                        'kosto_totale_page_per_punonjesin', 'department_id', 'employee_id', 'state']
            )
            if not contract_data:
                raise UserError(_('Cannot find any running contracts for the selected Department and Employee.'))

        elif department and not employee:
            contract_data = self.env['hr.contract'].search_read(
                domain=[
                    ('department_id', '=', department[0]),
                    ('state', '=', 'open')],
                fields=['wage', 'net', 'sig_shendetesore_punonjesi', 'sig_shoqerore_punonjesi',
                        'sig_shendetesore_punedhenesi', 'sig_shoqerore_punedhenesi', 'tatim_mbi_te_ardhurat',
                        'kosto_totale_page_per_punonjesin', 'department_id', 'employee_id', 'state']
            )
            if not contract_data:
                raise UserError(_('Cannot find any running contracts for the selected Department.'))

        elif employee and not department:
            contract_data = self.env['hr.contract'].search_read(
                domain=[
                    ('employee_id', '=', employee[0]),
                    ('state', '=', 'open')],
                fields=['wage', 'net', 'sig_shendetesore_punonjesi', 'sig_shoqerore_punonjesi',
                        'sig_shendetesore_punedhenesi', 'sig_shoqerore_punedhenesi', 'tatim_mbi_te_ardhurat',
                        'kosto_totale_page_per_punonjesin', 'department_id', 'employee_id', 'state']
            )
            if not contract_data:
                raise UserError(_('Cannot find any running contracts for the selected Employee.'))

        else:
            raise UserError(_('Please select at least one: Department, Employee.'))

        # Initialize total fields values
        total_net, total_wage, total_sigurime, total_tap, total_employee_monthly_cost = 0, 0, 0, 0, 0

        # Manipulate the contrat data for the report
        employees = []
        for record in contract_data:
            employee_name = record.get('employee_id')[1]
            department_name = record.get('department_id')[1]
            wage = int(record.get('wage')) if record.get('wage') else 0
            net = int(record.get('net')) if record.get('net') else 0
            sig_shendetesore_punonjesi = int(record.get('sig_shendetesore_punonjesi')) \
                if record.get('sig_shendetesore_punonjesi') else 0
            sig_shoqerore_punonjesi = int(record.get('sig_shoqerore_punonjesi')) \
                if record.get('sig_shoqerore_punonjesi') else 0
            sig_shendetesore_punedhenesi = int(record.get('sig_shendetesore_punedhenesi')) \
                if record.get('sig_shendetesore_punedhenesi') else 0
            sig_shoqerore_punedhenesi = int(record.get('sig_shoqerore_punedhenesi')) \
                if record.get('sig_shoqerore_punedhenesi') else 0
            sigurime = sum([sig_shendetesore_punonjesi, sig_shoqerore_punonjesi,
                                  sig_shendetesore_punedhenesi, sig_shoqerore_punedhenesi])
            tap = int(record.get('tatim_mbi_te_ardhurat')) if record.get('tatim_mbi_te_ardhurat') else 0
            employee_monthly_cost = int(record.get('kosto_totale_page_per_punonjesin')) \
                if record.get('kosto_totale_page_per_punonjesin') else 0

            total_net = total_net + net
            total_wage = total_wage + wage
            total_sigurime = total_sigurime + sigurime
            total_employee_monthly_cost = total_employee_monthly_cost + employee_monthly_cost
            total_tap = total_tap + tap

            vals = {
                'employee_name': employee_name,
                'department_name': department_name,
                'wage': wage,
                'net': net,
                'sigurime': sigurime,
                'tap': tap,
                'employee_monthly_cost': employee_monthly_cost,
                'total_net': total_net,
                'total_wage': total_wage,
                'total_sigurime': total_sigurime,
                'total_employee_monthly_cost': total_employee_monthly_cost,
                'total_tap': total_tap,
            }

            employees.append(vals)

        # Create PDF report
        if report_type == 'pdf':
            for item in employees:
                for k, v in item.items():
                    if isinstance(v, int):
                        item[k] = _format_integer(v)
                    else:
                        continue

            data = {
                'model': 'employee.monthly.cost.wizard',
                'form': self.read()[0],
                'employees': employees
            }
            return self.env.ref('hr_contracts_cp.action_employee_monthly_cost').with_context(
                landscape=True).report_action(self, data=data)
        else:
            # Create XLSX report
            # Create a new workbook and add a worksheet
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            document = workbook.add_format(
                {'border': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True,
                 'font_name': 'SansSerif', 'font_size': 10})

            document_1 = workbook.add_format(
                {'border': True, 'align': 'right', 'valign': 'vcenter', 'text_wrap': True,
                 'font_name': 'SansSerif', 'font_size': 10, 'num_format': '#,##0'})

            bold = workbook.add_format(
                {'bold': True, 'border': True, 'align': 'right', 'valign': 'vcenter',
                 'text_wrap': True,
                 'font_name': 'SansSerif', 'font_size': 10, 'num_format': '#,##0'})

            bold_header = workbook.add_format(
                {'bold': True, 'border': False, 'align': 'center', 'valign': 'vcenter',
                 'text_wrap': True, 'font_name': 'SansSerif', 'font_size': 13})

            header = workbook.add_format(
                {'bold': True, 'border': True, 'align': 'center', 'valign': 'vcenter',
                 'text_wrap': True,
                 'font_name': 'SansSerif', 'font_size': 10, 'bg_color': '#875A7B',
                 'color': 'white'})

            worksheet.merge_range('A%d:F%d' % (1, 1), "RAPORT KOSTO PAGE MUJORE", bold_header)

            worksheet.set_column('B:F', 17)
            worksheet.set_column('A:A', 5)
            worksheet.write('A3', 'Nr. ', header)
            worksheet.write('B3', 'Emer Mbiemer', header)
            worksheet.write('C3', 'Departamenti', header)
            worksheet.write('D3', 'Paga Bruto', header)
            worksheet.write('E3', 'Paga neto', header)
            worksheet.write('F3', 'Totali sigurime shoqerore', header)
            worksheet.write('G3', 'TAP', header)
            worksheet.write('H3', 'Kosto mujore punedhenesi', header)
            worksheet.set_default_row(15)

            nr_rendor = 1
            row = 3
            row_start = row
            col = 0

            for emp in employees:
                worksheet.write(row, col, nr_rendor, document)
                worksheet.write(row, col + 1, emp.get('employee_name'), document)
                worksheet.write(row, col + 2, emp.get('department_name'), document)
                worksheet.write(row, col + 3, emp.get('wage'), document_1)
                worksheet.write(row, col + 4, emp.get('net'), document_1)
                worksheet.write(row, col + 5, emp.get('sigurime'), document_1)
                worksheet.write(row, col + 6, emp.get('tap'), document_1)
                worksheet.write(row, col + 7, emp.get('employee_monthly_cost'), document_1)
                nr_rendor += 1

                row = row + 1

            worksheet.write(row, 2, 'Total', bold)
            worksheet.write(row, 3, employees[-1]['total_wage'], bold)
            worksheet.write(row, 4, employees[-1]['total_net'], bold)
            worksheet.write(row, 5, employees[-1]['total_sigurime'], bold)
            worksheet.write(row, 6, employees[-1]['total_tap'], bold)
            worksheet.write(row, 7, employees[-1]['total_employee_monthly_cost'], bold)

            workbook.close()

            # Encode the Excel file content using base64
            file_content_base64 = base64.b64encode(output.getvalue())

            # Create a new attachment record
            attachment = self.env['ir.attachment'].create({
                'name': 'raport_kosto_mujore_punonjesi.xlsx',
                'datas': file_content_base64,
                'res_model': 'employee.monthly.cost.wizard',
                'res_id': self.id,
            })

            # Return the attachment ID to open the file download wizard
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'self',
            }
