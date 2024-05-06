from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # !!! IMPORTANT !!! Be careful not to delete any of the selection types without consulting documentation
    # !!! IMPORTANT !!! Removing one of them from the code while ondelete policy is se to cascade may delete records associated with journals of that type
    type = fields.Selection(selection_add=[('landed_cost', 'Landed Cost'),
                                           ('closure', 'Closure'), # per fiscal year closure
                                           ('warehouse', 'Warehouse'),
                                           ('analytic_lines', 'Analytic Lines'),
                                           ('customs', 'Customs'),]
                            ,ondelete={'landed_cost': 'cascade',
                                       'closure': 'cascade',
                                       'warehouse': 'cascade',
                                       'analytic_lines': 'cascade',
                                       'customs': 'cascade', }, required=True)
    sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence',
                                  help="This field contains the information related to the numbering of the journal entries of this journal.",
                                  copy=False) #per pagesen e pagave
    closure_acc_id = fields.Many2one('account.account', string="Closure Account") # per fiscal year closure