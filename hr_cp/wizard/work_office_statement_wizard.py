from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import datetime
from io import BytesIO
import base64
import xlsxwriter


class WorkOfficeStatement(models.TransientModel):
    _name = 'work.office.statement.wizard'
    _description = 'Work Office Statement Wizard'

    company_id = fields.Many2one('res.company', required=True)
    department_id = fields.Many2one('hr.department', string='Department')
    report_type = fields.Selection([('pdf', 'Pdf'), ('xls', 'Excel')],
                                   string='Report Type',
                                   default='pdf',
                                   required=True)

    def work_office_statement(self):
        self.ensure_one()
        read = self.read()[0]

        # Get user input data
        company_id = read.get('company_id')[0]
        company_name = read.get('company_id')[1]
        department = read.get('department_id')
        report_type = read.get('report_type')

        # Get company data
        company_data = self.env['res.company'].search_read(
            domain=[('id', '=', company_id)],
            fields=['vat', 'partner_id', 'mobile', 'email',
                    'employer_name', 'company_start_date']
        )[0]

        vat = company_data.get('vat') if company_data.get('vat') else ''
        company_mobile = company_data.get('mobile') if company_data.get('mobile') else ''
        company_email = company_data.get('email') if company_data.get('email') else ''
        employer_name = company_data.get('employer_name') if company_data.get('employer_name') else ''
        company_start_date = company_data.get('company_start_date') if company_data.get('company_start_date') else ''
        company_partner = company_data.get('partner_id')[0] if company_data.get('partner_id') else None

        # Get company address
        if company_partner:
            company_address = self.env['res.partner'].search_read(
                domain=[('id', '=', company_partner)],
                fields=['street', 'city', 'zip', 'country_id']
            )[0]

            company_address = [
                company_address.get('street'),
                company_address.get('city'),
                company_address.get('zip'),
                company_address.get('country_id')[1] if company_address.get('country_id') else None]

            company_address = ', '.join(item for item in company_address if item)
        else:
            raise UserError(_('Please create or assign a contact for the company to fill the address.'))

        # Get Hr information
        hr_data = self.env['hr.employee'].search_read(
            domain=[('company_id', '=', company_id),
                    '|', ('job_id.name', 'ilike', 'human resources manager'),
                    ('job_id.name', 'ilike', 'shefe e burimeve njer')],
            fields=['name', 'mobile_phone', 'work_email']
        )

        if hr_data and len(hr_data) > 1:
            raise UserError(_('Multiple Human Resources Managers found, please assign only one.'))
        elif hr_data and len(hr_data) == 1:
            hr_data = hr_data[0]
            hr_name = hr_data.get('name') if hr_data.get('name') else ''
            hr_mobile = hr_data.get('mobile_phone') if hr_data.get('mobile_phone') else ''
            hr_work_mail = hr_data.get('work_email') if hr_data.get('work_email') else ''
        else:
            raise UserError(_('Please create or assign a Human Resources Manager.'))

        # Create employee domain
        if department:
            employee_domain = [('company_id', '=', company_id), ('department_id', '=', department[0])]
        else:
            employee_domain = [('company_id', '=', company_id)]

        # Get total employee and female employee count
        total_employees = self.env['hr.employee'].search_count(
            domain=employee_domain
        )
        female_employees = self.env['hr.employee'].search_count(
            domain=employee_domain + [('gender', '=', 'female')]
        )

        # Get employee data
        employee_data = self.env['hr.employee'].search_read(
            domain=employee_domain,
            fields=['name', 'ssnid', 'birthday', 'private_street', 'private_city', 'private_zip',
                    'private_country_id', 'department_id', 'job_id', 'father_name', 'employee_origin_id', 'certificate']
        )

        # Initialize employees for the report
        employees = []

        if employee_data:
            for emp in employee_data:
                employee_name = emp.get('name') if emp.get('name') else ''
                if len(employee_name) <= 1:
                    raise UserError(_(f'Please enter the correct First and Last name for the employee {employee_name}'))

                employee_ssnid = emp.get('ssnid') if emp.get('ssnid') else ''
                employee_birthday = emp.get('birthday') if emp.get('birthday') else ''
                employee_address = [
                    emp.get('private_street') if emp.get('private_street') else '',
                    emp.get('private_city') if emp.get('private_city') else '',
                    emp.get('private_zip') if emp.get('private_zip') else '',
                    emp.get('private_country_id')[1] if emp.get('private_country_id') else '',
                ]
                employee_address = ', '.join(item for item in employee_address if item)
                employee_department = emp.get('department_id')[1] if emp.get('private_country_id') else ''
                employee_job = emp.get('job_id')[1] if emp.get('job_id') else ''
                employee_education = emp.get('certificate').capitalize() if emp.get('certificate') else ''
                employee_father_name = emp.get('father_name')
                if employee_father_name:
                    employee_name = employee_name.split()
                    employee_name = f' {employee_father_name} '.join(employee_name)

                employee_origin = emp.get('employee_origin_id')[1] if emp.get('employee_origin_id') else ''

                # Get employee start date
                employee_contract = self.env['hr.contract'].search_read(
                    domain=[('employee_id', '=', emp.get('id')), ('state', '!=', 'closed')],
                    fields=['date_start']
                )

                if employee_contract:
                    employee_start_date = [
                        contract.get('date_start') for contract in employee_contract
                    ]
                    employee_start_date = min(employee_start_date)
                else:
                    raise UserError(_(f'The employee {employee_name} does not have any contracts assigned.'))

                vals = {
                    'employee_name': employee_name,
                    'employee_ssnid': employee_ssnid,
                    'employee_birthday': employee_birthday,
                    'employee_address': employee_address,
                    'employee_department': employee_department,
                    'employee_job': employee_job,
                    'employee_education': employee_education,
                    'employee_start_date': employee_start_date,
                    'employee_origin': employee_origin,
                }

                employees.append(vals)
        else:
            raise UserError(_('No employee records found with the specified Company and Department.'))

        # Report data
        data = {
            'company_name': company_name,
            'company_address': company_address,
            'vat': vat,
            'company_mobile': company_mobile,
            'company_email': company_email,
            'employer_name': employer_name,
            'company_start_date': company_start_date,
            'hr_name': hr_name,
            'hr_mobile': hr_mobile,
            'hr_work_mail': hr_work_mail,
            'total_employees': total_employees,
            'female_employees': female_employees,
            'employees': employees
        }

        if report_type == 'pdf':
            # Create PDF report
            return self.env.ref('hr_cp.action_work_office_statement').with_context(landscape=True).report_action(self, data=data)

        else:
            # Create XLSX report
            # Create a new workbook and add a worksheet
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # Styling
            center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': True})

            text_bold = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True,
                                             'font_name': 'SansSerif', 'font_size': 10, 'num_format': '#,##0'})

            document = workbook.add_format({'border': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True,
                                            'font_name': 'SansSerif', 'font_size': 10})

            bold = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'text_wrap': True,
                                        'font_name': 'SansSerif', 'font_size': 10, 'num_format': '#,##0'})

            bold_header = workbook.add_format({'bold': True, 'border': False, 'align': 'center', 'valign': 'vcenter',
                                               'text_wrap': True, 'font_name': 'SansSerif', 'font_size': 15})

            header = workbook.add_format(
                {'bold': True, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
                 'font_name': 'SansSerif', 'font_size': 10, 'bg_color': '#875A7B', 'color': 'white'})

            worksheet.merge_range('A%d:I%d' % (1, 1), "DREJTORIA RAJONALE E SHËRBIMIT KOMBËTAR TË PUNËSIMIT TIRANË",
                                  bold_header)

            worksheet.merge_range('A%d:I%d' % (3, 3), f"SUBJEKTI DEKLARUES: " + data.get("company_name"), bold)
            worksheet.merge_range('A%d:I%d' % (4, 4), "NIPT: " + (data.get("vat")), bold)
            worksheet.merge_range('A%d:I%d' % (5, 5), "Adresa e subjektit: " + data.get("company_address"), bold)
            worksheet.merge_range('A%d:I%d' % (6, 6), "Emri i punedhenesit: " + data.get("employer_name"), bold)
            worksheet.merge_range('A%d:I%d' % (7, 7), "Tel: " + data.get("company_mobile") + " Email: " + data.get("company_email"),
                                  bold)
            worksheet.merge_range('A%d:I%d' % (8, 8),
                                  "Data e fillimit te aktivitetit: " + data.get("company_start_date"), bold)
            worksheet.merge_range('A%d:I%d' % (9, 9),
                                  "Personi kontaktues: " + (data.get("hr_name")) + " Tel: " + (
                                      data.get("hr_mobile")) + " Email: " + (data.get("hr_work_mail")),
                                  bold)
            worksheet.merge_range('A%d:I%d' % (10, 10),
                                  "Totali punonjes: " + str(data.get("total_employees")) +
                                  " Totali Femra: " + str(data.get("female_employees")), text_bold)
            worksheet.merge_range('A%d:I%d' % (11, 11), '', text_bold)

            worksheet.set_column('B:H', 17)
            worksheet.set_column('I:I', 20)
            worksheet.set_column('A:A', 5)
            worksheet.write('A12', 'Nr. ', header)
            worksheet.write('B12', 'Nr. i siguracionit ', header)
            worksheet.write('C12', 'Emer Atesi Mbiemer', header)
            worksheet.write('D12', 'Datelindje dd/mm/yyyy', header)
            worksheet.write('E12', 'Arsimi', header)
            worksheet.write('F12', 'Profesioni qe ushtron', header)
            worksheet.write('G12', 'Data e fillimit te punes ne firme', header)
            worksheet.write('H12', 'Adresa e sakte e banimit', header)
            worksheet.write('I12',
                            'Nga vjen personi kur vjen ne pune:Papunesia,Pag/Papunesie,Nd/ekonomike,Per here te pare,Te tjera ',
                            header)
            worksheet.set_default_row(15)

            nr_rendor = 0
            row = 12
            col = 0

            for emp in data.get('employees'):
                nr_rendor = nr_rendor + 1
                worksheet.write(row, col, nr_rendor, document)
                worksheet.write(row, col + 1, emp.get('employee_ssnid'), document)
                worksheet.write(row, col + 2, emp.get('employee_name'), document)
                worksheet.write(row, col + 3, emp.get('employee_birthday'), document)
                worksheet.write(row, col + 4, emp.get('employee_education'), document)
                worksheet.write(row, col + 5, emp.get('employee_job'), document)
                worksheet.write(row, col + 6, emp.get('employee_start_date'), document)
                worksheet.write(row, col + 7, emp.get('employee_address'), document)
                worksheet.write(row, col + 8, emp.get('employee_origin'), document)
                row = row + 1

            workbook.close()

            # Encode the Excel file content using base64
            file_content_base64 = base64.b64encode(output.getvalue())

            # Create a new attachment record
            attachment = self.env['ir.attachment'].create({
                'name': 'raport_deklarimi_per_zyren_e_punes.xlsx',
                'datas': file_content_base64,
                'res_model': 'deklarimi.zyra.punes.wizard',
                'res_id': self.id,
            })

            # Return the attachment ID to open the file download wizard
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'self',
            }

