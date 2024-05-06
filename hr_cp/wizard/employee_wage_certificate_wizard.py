from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime
import inflect


def format_salary(salary):
    p = inflect.engine()
    return p.number_to_words(salary)


def translate_salary(salary):

    shqip = {
        'zero': 'zero',
        'one': 'një',
        'two': 'dy',
        'three': 'tre',
        'four': 'katër',
        'five': 'pesë',
        'six': 'gjashtë',
        'seven': 'shtatë',
        'eight': 'tetë',
        'nine': 'nëntë',
        'ten': 'dhjetë',
        'twenty': 'njëzetë',
        'thirty': 'tridhjetë',
        'forty': 'dyzetë',
        'fifty': 'pesëdhjete',
        'sixty': 'gjashtëdhjetë',
        'seventy': 'shtatëdhjetë',
        'eighty': 'tetëdhjetë',
        'ninty': 'nëntëdhjetë',
        'hundred': 'qind',
        'thousand': 'mijë',
        'million': 'milion',
        'billion': 'bilion',
    }

    for key, value in shqip.items():
        if key in salary:
            salary = salary.replace(key, shqip[key])

    salary = salary.replace(',', ' e').replace('-', ' e ').replace('and', 'e')

    return salary


class EmployeeWageCertificate(models.TransientModel):
    _name = 'employee.wage.certificate.wizard'
    _description = 'Employee wage certificate wizard'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date = fields.Date('Date')

    def employee_wage_certificate_report(self):
        self.ensure_one()
        read = self.read()[0]

        employee_id = read.get('employee_id')[0]
        report_date = read.get('date')
        report_date = datetime.strptime(str(report_date), '%Y-%m-%d').strftime('%d/%m/%Y') \
            if report_date else ''

        employee_data = self.env['hr.employee'].search_read(
            domain=[('id', '=', employee_id), ('contract_id', '!=', False)],
            fields=['name', 'company_id', 'contract_id', 'job_id', 'ssnid']
        )

        if employee_data:
            employee_data = employee_data[0]
            # Employee fields
            employee_name = employee_data.get('name')
            company_id = employee_data.get('company_id')[0] if employee_data.get('company_id') else None
            company_name = employee_data.get('company_id')[1] if employee_data.get('company_id') else None
            contract_id = employee_data.get('contract_id')[0]
            employee_job = employee_data.get('job_id')[1] if employee_data.get('job_id') else ''
            employee_ssnid = employee_data.get('ssnid') if employee_data.get('ssnid') else ''

            if company_id:

                # Company fields
                company_data = self.env['res.company'].search_read(
                    domain=[('id', '=', company_id)],
                    fields=['vat', 'email', 'phone', 'mobile', 'partner_id']
                )[0]

                company_vat = company_data.get('vat') if company_data.get('vat') else ''
                company_email = company_data.get('email') if company_data.get('email') else ''
                company_phone = company_data.get('phone') if company_data.get('phone') else ''
                company_mobile = company_data.get('mobile') if company_data.get('mobile') else ''
                company_duns = company_data.get('duns') if company_data.get('duns') else ''
                company_standard = company_data.get('standard') if company_data.get('standard') else ''
                company_partner_id = company_data.get('partner_id')[0] if company_data.get('partner_id') else ''
            else:
                raise ValidationError(_('The employee is not linked with a company.'))

            if company_partner_id:
                # Company address fields
                partner_data = self.env['res.partner'].search_read(
                    domain=[('id', '=', company_partner_id)],
                    fields=['street', 'city', 'zip', 'country_id']
                )[0]

                company_street = partner_data.get('street') if partner_data.get('street') else ''
                company_city = partner_data.get('city') if partner_data.get('city') else ''
                company_zip = partner_data.get('zip') if partner_data.get('zip') else ''
                company_country = partner_data.get('country_id')[1] if partner_data.get('country_id') else ''
                company_address = [company_street, company_city, company_zip, company_country]
                company_address = ', '.join(item for item in company_address if item)
            else:
                raise ValidationError(_('The company is not linked with a partner.'))

            # Contract fields
            contract_data = self.env['hr.contract'].search_read(
                domain=[('id', '=', contract_id)],
                fields=['date_start', 'date_end', 'wage', 'net', 'hr_responsible_id']
            )[0]

            date_start = contract_data.get('date_start') if contract_data.get('date_start') else ''
            date_start = datetime.strptime(str(date_start), '%Y-%m-%d').strftime('%d/%m/%Y') \
                if date_start else ''
            date_end = contract_data.get('date_end') if contract_data.get('date_end') else ''
            date_end = datetime.strptime(str(date_end), '%Y-%m-%d').strftime('%d/%m/%Y') \
                if date_end else 'sot'
            wage = contract_data.get('wage') if contract_data.get('wage') else 0
            wage_text = format_salary(int(float(wage)))
            wage_translated = translate_salary(wage_text)
            net = contract_data.get('net') if contract_data.get('net') else 0
            net_text = format_salary(int(float(net)))
            net_translated = translate_salary(net_text)
            hr_responsible_id = contract_data.get('hr_responsible_id')[0] if contract_data.get('hr_responsible_id') else None
            hr_responsible_name = contract_data.get('hr_responsible_id')[1] if contract_data.get('hr_responsible_id') else None

            if hr_responsible_id:
                # Hr responsible fields
                hr_responsible_data = self.env['hr.employee'].search_read(
                    domain=[('user_id', '=', hr_responsible_id)],
                    fields=['work_email', 'mobile_phone']
                )[0]

                hr_responsible_email = hr_responsible_data.get('work_email') if hr_responsible_data.get('work_email') else ''
                hr_responsible_mobile = hr_responsible_data.get('mobile_phone') if hr_responsible_data.get('mobile_phone') else ''
            else:
                raise ValidationError(_('The selected employee does not have a HR responsible.'))

            # Report data
            data = {
                'report_date': report_date,
                'employee_name': employee_name,
                'company_name': company_name,
                'employee_job': employee_job,
                'employee_ssnid': employee_ssnid,
                'company_vat': company_vat,
                'company_email': company_email,
                'company_phone': company_phone,
                'company_mobile': company_mobile,
                'company_duns': company_duns,
                'company_standard': company_standard,
                'company_address': company_address,
                'date_start': date_start,
                'date_end': date_end,
                'wage': wage,
                'wage_translated': wage_translated,
                'net': net,
                'net_translated': net_translated,
                'hr_responsible_name': hr_responsible_name,
                'hr_responsible_email': hr_responsible_email,
                'hr_responsible_mobile': hr_responsible_mobile,

            }

            return self.env.ref('hr_cp.action_employee_wage_certificate').report_action(self, data=data)

        else:
            raise ValidationError(_('The selected employee does not have a contract.'))

