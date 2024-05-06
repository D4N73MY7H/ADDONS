from odoo import models, fields, api, Command, _
import time
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp

class HrPyslipPayment(models.Model):
    _name='hr.payslip.payment'
    _description = 'Payslip Payment'


    name =fields.Char(string='Description', size=64, required=True, readonly=True)
    note =fields.Text(string='Note' )
    company_id =fields.Many2one('res.company', 'Company', required=False, readonly=True, default=lambda self: self.env.user.company_id,)
    date= fields.Date(string='Payment Date', default=lambda *a: time.strftime('%Y-%m-%d'), required=True,)
    bank_journal_id = fields.Many2one('account.journal', string="Cash/Bank Journal" , required=True,)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches',required=True)
    payment_line_ids = fields.One2many('payslip.payment.line', 'payslip_payment_id', string='Payslip lines',)
    move_line_ids = fields.One2many('account.move.line', 'payslip_payment_id', string='Move Entry Lines')
    state= fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Canceled'),
    ], 'State', index=True, readonly=True,default='draft',
        help='* When the payslip payment is created the state is \'Draft\'.\
            \n* If the payslip payment is processed then state is set to \'Done\'.\
            \n* When user cancel payslip payment the state is \'Canceled\'.')

    def unlink(self):
        for payment in self:
            if payment.state != 'draft':
                raise UserError(("You cannot delete payment '%s'; it must be in state 'Draft' to be deleted. " \
                                 "You should better cancel it, instead of deleting it.") % payment.name)
            return super(HrPyslipPayment,self).unlink()

    @api.onchange('payslip_run_id', 'bank_journal_id')
    def onchange_payslip_run_id(self):
        # Fetch payslips from the selected payslip run
        payslips = [slip for slip in self.payslip_run_id.slip_ids if slip.state == 'done' and slip.net_residual]
        payment_lines_to_create = []
        #Delete the line which exists
        if self.payment_line_ids:
            print("===DELETED===")
            self.payment_line_ids = [(5, 0, self.payment_line_ids)]

        # Loop through each payslip and create payment lines
        for payslip in payslips:
            if hasattr(payslip.employee_id, 'bank_journal_id') and payslip.employee_id.bank_journal_id:
                bank_journal_id1 = payslip.employee_id.bank_journal_id.id
            else:
                bank_journal_id = self.bank_journal_id


            payment_line_data = {
                'payslip_id': payslip.id,
                'name': payslip.name,
                'account_id': payslip.employee_id.llogarit_kontabel.id,
                'net_amount': payslip.net_total,
                'remaining_amount': payslip.net_residual,
                'payment_amount': payslip.net_residual,
                'bank_journal_id': bank_journal_id if bank_journal_id else  bank_journal_id1,
            }

            payment_lines_to_create.append((0, 0, payment_line_data))


        # Update the payment_line_ids field with the new payment lines
        self.payment_line_ids = payment_lines_to_create

    def confirm_payment(self, context=None):
        for payment in self:
            for payment_line in payment.payment_line_ids:
                payslip_payed = False

                # Cekojme nese vlerat jan te barabarta ather ndryshojm booleanin

                if payment_line.payment_amount == payment_line.remaining_amount:
                    payslip_payed = True
                elif payment_line.payment_amount > payment_line.remaining_amount:
                    raise UserError("Your payment cannot exceed remaining amount")
                elif payment_line.payment_amount <= 0:
                    raise UserError("Your payment cannot be negative or zero")
                if payment_line.bank_journal_id.sequence_id:
                    st_number = payment_line.bank_journal_id.sequence_id.next_by_id()
                else:
                    raise UserError(
                        _('Error: Payment journal must have a sequence linked to %s') % payment_line.bank_journal_id.name)
                self.create_move_from_st_line(payment_line.id, st_number, context)

                if payslip_payed:
                    payment_line.payslip_id.write({'state': 'paid'})
                payment_line.write({'remaining_amount': payment_line.remaining_amount - payment_line.payment_amount})

            return self.write({'state': 'done'})

    def create_move_from_st_line(self, payment_line_id, st_number,context=None):
        if context is None:
            context={}
        account_move_obj = self.env['account.move']
        paylsip_payment_line_obj = self.env['payslip.payment.line']

        #id-ja cdo linje ne objekt
        payment_line = paylsip_payment_line_obj.browse(int(payment_line_id))


        #marrim id per objektin e modelit ton
        payment = payment_line.payslip_payment_id



         #marrim llogarin e bankes qe gjendet ne modelin ton
        account_id = payment_line.bank_journal_id.default_account_id.id

        val = {
            'name': payment_line.name,
            'date': payment.date,
            'ref': st_number,
            'partner_id': False,
            'account_id': account_id,
            'payslip_payment_id': payment.id,
            'journal_id': payment_line.bank_journal_id.id,
            'credit': payment_line.payment_amount,
            'debit': 0,
            'payslip_id': payment_line.payslip_id.id,

        }
        if not payment_line.payslip_id.employee_id.llogarit_kontabel:
            raise UserError("Employee must be linked with an account")

        val_second_line = {
            'name': payment_line.name,
            'date': payment.date,
            'ref': st_number,
            'partner_id': False,
            'account_id': payment_line.payslip_id.employee_id.llogarit_kontabel.id,
            'payslip_payment_id': payment.id,
            'journal_id': payment_line.bank_journal_id.id,
            'debit': payment_line.payment_amount,
            'payslip_id': payment_line.payslip_id.id,
        }

        move_id = account_move_obj.create({
            'journal_id': payment_line.bank_journal_id.id,
            'date': payment.date,
            'name': st_number,
            'ref': st_number,
            'line_ids': [(0, 0, val), (0, 0, val_second_line)],

        })

        move_id.action_post()
        return move_id


    def cancel_payment(self):
        for payment in self:
            move_ids = []
            for line in payment.move_line_ids:
                if line.move_id not in move_ids:
                    if not line.move_id in move_ids:
                        move_ids.append(line.move_id)
                        print(move_ids)
            for move_id in move_ids:
                move_id.button_cancel()
                move_id.unlink()
            for payment_line in payment.payment_line_ids:
                payment_line.write({'remaining_amount': payment_line.remaining_amount + payment_line.payment_amount})
                payment_line.payslip_id.write({'state': 'done'})
        return self.write({'state': 'cancel'})

    def set_draft(self):
        return self.write({'state': 'draft'})

class PyslipPaymentLine(models.Model):
    _name = 'payslip.payment.line'
    _description = 'Payslip Payment Lines'

    name = fields.Char(string='Description', size=64,)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip',required=True)
    account_id = fields.Many2one('account.account',string='Account Id')
    net_amount = fields.Float(string='Net Amount', digits=dp.get_precision('Payroll'), compute="tot_net",readonly=True, )
    remaining_amount = fields.Float(string='Remaining Amount', digits=dp.get_precision('Payroll'),compute="tot_net", readonly=True, )
    payment_amount = fields.Float(string='Payment Amount', digits=dp.get_precision('Payroll'))
    payslip_payment_id = fields.Many2one('hr.payslip.payment', string='Payslip Payment',ondelete='cascade')
    bank_journal_id = fields.Many2one('account.journal', string="Cash/Bank Journal",required=True)

    @api.depends('payslip_id')
    def tot_net(self):
        for rec in self:
            rec.net_amount = 0
            rec.remaining_amount = 0
            if rec.payslip_id:
                net_amount = 0
                for line in rec.payslip_id.line_ids:
                    if line.category_id.code == 'NET':
                        net_amount += line.amount
                rec.net_amount = net_amount
                rec.remaining_amount = rec.payslip_id.net_residual
                #marrim vleren nga fusha compute net_residual ==> hr.payslip
                #mbushet automatikisht kur plotsohen linjat