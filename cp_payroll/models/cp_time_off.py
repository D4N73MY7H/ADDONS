from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class CPHolidaysType(models.Model):
    _inherit = "hr.leave.type"

    payroll_rate = fields.Float(string='Payroll Rate', default=100)


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    change_amount = fields.Boolean('Change the Value', default=False)

    @api.depends('is_paid', 'number_of_hours','payslip_id','payslip_id.sum_worked_hours')
    def _compute_amount(self):
        # if change amount is true the amount field is editable and saves the changed value otherwise the computed value remains the same
        for worked_days in self:
            if not worked_days.payslip_id.edited and not worked_days.change_amount:
                payslip = worked_days.payslip_id
                struct_id = payslip.struct_id
                if not struct_id:
                    raise ValidationError("Structure is not defined for the payslip.")

                if not struct_id.avarage_days:
                    raise ValidationError("Average days are not defined in the payslip structure.")

                if struct_id.avarage_days:
                    # ditet mesatare te punes qe ndodhen ne strukture
                    avg_work_days = struct_id.avarage_days

                    # oret mesatare te punes qe ndodhen ne fushen me emer Working Schedule pas kontrates
                    avg_work_hours = payslip.contract_id.resource_calendar_id.hours_per_day


                    working_hours = avg_work_hours * avg_work_days

                    # nese ska kontrat dhe 1 nga kto codet gjended athere shuma do jet prap 0
                    if worked_days.contract_id or worked_days.code not in ['OUT', 'MATERNITY', 'LEAVE90']:
                        if worked_days.payslip_id.wage_type == "hourly":
                            hourly_wage = payslip.contract_id.hourly_wage if worked_days.is_paid else 0
                            worked_days.amount = round(hourly_wage * worked_days.number_of_hours, 0)
                        else:
                            if worked_days.code != 'WORK100':
                                contract_wage = payslip.contract_id.contract_wage if worked_days.is_paid else 0
                                worked_days.amount = round(contract_wage * worked_days.number_of_hours / working_hours,0)
                            else:
                                not_working100_hours = sum(line.number_of_hours for line in payslip.worked_days_line_ids if line.code != 'WORK100')
                                number_of_hours = working_hours - not_working100_hours if not_working100_hours else working_hours
                                print(not_working100_hours,"Not working hours")
                                print(working_hours,"Working hours")
                                print(number_of_hours,"Number of hours")
                                worked_days.amount = payslip.contract_id.contract_wage * number_of_hours / working_hours if worked_days.is_paid else 0

                    else:
                        worked_days.amount = 0
                    # Kërkojmë llojet e pushimeve bazuar në 'work_entry_type_id' të lidhur me 'worked_days.'

                    leave_types = self.env['hr.leave.type'].search_read([('work_entry_type_id', '=', worked_days.work_entry_type_id.id)], limit=1)
                    if leave_types:
                        # Nëse gjejmë lloje të pushimeve, llogarisim 'payroll_rate' dhe përditësojmë 'amount' në përputhje me përqindjen e pagës së përditësuar.
                        payroll_rate = leave_types[0]['payroll_rate']

                        worked_days.amount = fields.Float.round(worked_days.amount * (payroll_rate / 100),0)

                    else:
                        worked_days.amount = 0
                else:
                    # Nëse nuk ka një vlerë 'avarage_days' në strukturën e pagesës, kryejmë një llogaritje të thjeshtë bazuar në llojin e pagesës dhe varësinë e numrit të orëve.
                    if worked_days.contract_id or worked_days.code not in ['OUT', 'MATERNITY', 'LEAVE90']:
                        if worked_days.payslip_id.wage_type == "hourly":
                            worked_days.amount = fields.Float.round(
                                payslip.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0,0)
                        else:
                            sum_worked_hours = payslip.sum_worked_hours or 1
                            worked_days.amount = fields.Float.round(
                                worked_days.payslip_id.contract_id.contract_wage * worked_days.number_of_hours / sum_worked_hours if worked_days.is_paid else 0,0)

                            leave_types = self.env['hr.leave.type'].search_read(
                                [('work_entry_type_id', '=', worked_days.work_entry_type_id.id)], limit=1)
                            if leave_types:
                                payroll_rate = leave_types[0].get('payroll_rate', 100)
                                worked_days.amount = fields.Float.round(worked_days.amount * (payroll_rate / 100), 0)
                            else:
                                worked_days.amount = 0
                    else:
                         worked_days.amount = 0


