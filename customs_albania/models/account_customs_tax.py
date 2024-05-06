from odoo import models, fields, api


class TaxLinesCP(models.Model):
    _name = 'account.customs.tax'

    customs_id = fields.Many2one('account.customs', string='Customs Entry',
                                 index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",
                                 check_company=True,
                                 help="The move of this entry line.")

    move_type_line = fields.Selection(related='customs_id.move_type', store=True)
    tax_id = fields.Many2one('account.tax', 'Tax', ondelete='restrict')
    account_id = fields.Many2one('account.account', string='Account', )
    journal_id = fields.Many2one('account.journal', 'Journal', ondelete='set null')
    base_price = fields.Float('Tax Base')
    tax_amount = fields.Float('Tax Amount')
    import_type = fields.Selection([
        ('mallra20', 'Import mallra 20%'),
        ('mallra0', 'Import mallra te perjashtuar'),
        ('asete20', 'Import asete 20%'),
        ('asete0', 'Import asete te perjashtuar'),
        ('mallra10', 'Import mallra 10%'),
        ('mallra6', 'Import mallra 6%'),
    ], 'Shfaq ne liber blerje')
    export_type = fields.Selection([('export0', 'Eksport me 0%')], 'Shfaq ne liber shitje')
    partner_id = fields.Many2one('res.partner', string='Partner', related='customs_id.partner_id', store=True,
                                 readonly=True, related_sudo=False)
    date = fields.Date(string='Date', related='customs_id.date', store=True, readonly=True, related_sudo=False)
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')

    product_id = fields.Many2one('product.product', string='Product')

    @api.onchange('tax_id')
    def _onchange_tax_id(self):
        tax = self.tax_id
        if not tax:
            self.account_id = False
        else:
            self.account_id = tax.invoice_repartition_line_ids[1].account_id and tax.invoice_repartition_line_ids[1].account_id.id or False