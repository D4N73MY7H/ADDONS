# -*- coding:utf-8 -*-
import time
import math
from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from datetime import datetime,timedelta,date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class FiscalYearClosure(models.Model):
    _name = "fiscal.year.closure"


    def _get_closure_journal(self):
        journal_id = self.env['account.journal'].search([('type', '=', 'closure')], limit=1)
        if not journal_id.exists():
            raise ValidationError(_('The closure journal does not exist!'))
        return journal_id


    name = fields.Char(string='Name',required=True)
    year = fields.Selection([(str(year),str(year)) for year in range(2000,date.today().year + 10)], string="Year")
    state = fields.Selection([('draft', 'New'), ('confirm', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancel')],
                             'State', readonly=True, required=True, default='draft')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,default=_get_closure_journal)
    move_line_ids = fields.One2many('account.move.line','fiscal_closure_id',string='Move Entries')


    def button_confirm(self):
        account_move = self.env['account.move']
        account_closure = self.journal_id.closure_acc_id.id
        balance_income = 0
        balance_expense = 0
        vals = []
        date_start = '%s-12-31'% str(int(self.year) - 1)
        date_end = '%s-01-01'% str(int(self.year) + 1)
        account_ids_expense = self.env["account.account"].search([('code', '=ilike', ('6%'))])
        account_ids_income = self.env["account.account"].search([('code', '=ilike', ('7%'))])
        for account in account_ids_expense:
            income_domain = [('account_id', '=', account.id),
                          ('date', '>', date_start),
                          ('date', '<', date_end),
                          ('parent_state', '=', 'posted'),
                          ('debit', '!=', False),
                          ('credit', '!=', False)]
            aml = self.env["account.move.line"].search(income_domain)
            balance = sum(aml.mapped('debit')) - sum(aml.mapped('credit'))
            if balance and balance != 0:
                data = ({
                    'name': account.name or '/',
                    'debit': abs(balance) if balance < 0 else 0,
                    'credit': balance if balance > 0 else 0,
                    'account_id': account.id,
                    'journal_id': self.journal_id.id,
                    'date': '%s-12-31' % self.year,
                    'fiscal_closure_id': self.id,
                })
                vals.append(data)
                balance_expense += balance

        for account in account_ids_income:
            expense_domain = [('account_id', '=', account.id),
                             ('date', '>', date_start),
                             ('date', '<', date_end),
                             ('parent_state', '=', 'posted'),
                             ('debit', '!=', False),
                             ('credit', '!=', False)]
            aml = self.env["account.move.line"].search(expense_domain)
            balance = sum(aml.mapped('debit')) - sum(aml.mapped('credit'))
            if balance and balance != 0:
                data = ({
                    'name': account.name or '/',
                    'debit': abs(balance) if balance < 0 else 0,
                    'credit': balance if balance > 0 else 0,
                    'account_id': account.id,
                    'journal_id': self.journal_id.id,
                    'amount_currency': 0.0,
                    'date': '%s-12-31' % self.year,
                    'fiscal_closure_id': self.id,
                })
                vals.append(data)
                balance_income += balance

        balance_expense = abs(balance_expense)

        balance_income = abs(balance_income)

        data=({
             'name': 'Fical Year Closure' or '/',
            'debit': abs(balance_income - balance_expense) if balance_income < balance_expense else 0,
            'credit': abs(balance_income - balance_expense) if balance_income > balance_expense else 0,
            'account_id': account_closure,
            'journal_id': self.journal_id.id,
            'date': '%s-12-31'% self.year,
            'fiscal_closure_id': self.id,
        })
        vals.append(data)


        move = {
            'ref': self.name,
            'journal_id': self.journal_id.id,
            'date': '%s-12-31' % self.year,
            'line_ids': [(0, 0, val) for val in vals]
        }

        move_id = account_move.with_context(check_move_validity=False,skip_invoice_sync=True).create(move)
        self.write({'state':'confirm'})
        return True


    def button_post(self):
        if self.move_line_ids:
            move_ids = set(move_line.move_id.id for move_line in self.move_line_ids)
            move_objs = self.env['account.move'].browse(move_ids)
            move_objs.action_post()
        self.write({'state': 'done'})
        return True

    def action_draft(self):
        self.write({'state':'draft'})

    def button_cancel(self):
        if self.move_line_ids:
            move_ids = set(move_line.move_id.id for move_line in self.move_line_ids)
            move_object = self.env['account.move'].browse(move_ids)
            for move in move_object:
                if self.state == 'done':
                    move.button_cancel()
                move.unlink()
        self.write({'state': 'cancel'})

    def unlink(self):
        if self.state != 'draft':
            raise UserError('Warning !' 'You can\'t delete a record that is not in draft state')
        return super(FiscalYearClosure, self).unlink()
