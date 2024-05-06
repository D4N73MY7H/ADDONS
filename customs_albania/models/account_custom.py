from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


class CustomsCP(models.Model):
    _name = 'account.customs'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'sequence.mixin']
    _description = "Customs documents"

    def _default_location_id(self):
        return self._get_default_location_id('Vendor', 'Stock')

    def _default_location_destination_id(self):
        return self._get_default_location_id('Stock', 'Customers')

    def _get_default_location_id(self, first_location, second_location):
        default_move_type = self._context.get('default_move_type', None)
        location_name = first_location if default_move_type in ['import', 'in_invoice'] else second_location
        return self.env['stock.location'].search([('name', 'like', location_name)], limit=1).id

    sequence_nr = fields.Char('Sequence Number',
                              default=lambda self: self.env['ir.sequence'].next_by_code('account.customs'))

    delivery_count = fields.Integer(string='Delivery Count', default=0, compute='_count_delivery_documents')

    journal_entries_count = fields.Integer(string='Journal Entries', default=0, compute='_count_journal_entries')

    landed_costs_count = fields.Integer(string='Landed Costs Count', default=0, compute='_count_landed_costs')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, default='draft')

    move_type = fields.Selection(selection=[
        ('entry', 'Journal Entry'),
        ('import', 'Import'),
        ('export', 'Export')
    ], string='Type', required=True, store=True, index=True, readonly=True, tracking=True,
        default="entry", change_default=True)

    name = fields.Char(string="Document Number", required=True)

    partner_id = fields.Many2one('res.partner', string="Partner")
    date = fields.Date(string="Date", required=True, default=datetime.today())
    date_in_report = fields.Date(string="Date in Report")
    post_in_journals = fields.Boolean(string="Post in Journals", default=True)
    create_account_move = fields.Boolean(string="Create account moves", default=True)

    location_id = fields.Many2one('stock.location', string="Location", required=True, default=_default_location_id)
    location_destination_id = fields.Many2one('stock.location', string="Destination Location", required=True,
                                              default=_default_location_destination_id)
    related_invoice_id = fields.Many2one('account.move', string="Related Documents")

    customs_line_ids = fields.One2many('account.customs.line', 'customs_id', string='Customs lines')
    tax_line_ids = fields.One2many('account.customs.tax', 'customs_id', string='Tax lines')

    def action_confirm(self):
        for doc in self:
            for line in doc.customs_line_ids:
                if line.product_id_line.detailed_type != 'product':
                    raise UserError(_('You cannot create inventory move.\nAll lines should contain stock products.'))

            total_tax = sum(tax_line.tax_amount for tax_line in doc.tax_line_ids)

            if len(self.tax_line_ids.ids) > 0 and total_tax > 0:
                self.create_tax_move()

            if doc.move_type == 'import' and len(self.customs_line_ids.ids) > 0:
                self.create_import_stock_move()
            else:
                if len(self.customs_line_ids.ids) > 0:
                    self.create_export_stock_move()

            doc.state = 'done'

    def create_tax_move(self):
        journal_selected = self.tax_line_ids[-1].journal_id
        document_result = self.env['account.move'].create({
            'move_type': 'entry',
            # 'name': journal_selected.code + '/' + str(datetime.today().year) + '/' + month_prefix + str(datetime.now().month) + '/' + str(self.sequence_nr),
            'name': journal_selected.code + '/' + str(self.sequence_nr),
            'journal_id': journal_selected.id,
            'date': self.date,
            'ref': self.name,
            'state': 'draft'
        })
        for line in self.tax_line_ids:
            if line.tax_amount > 0:
                # Credit & Debit action
                document_result['line_ids'] = [(0, 0, {
                    'account_id': line.journal_id.customs_account_id.id,
                    'partner_id': document_result.partner_id.id,
                    'name': self.name,
                    'credit': line.tax_amount,
                }), (0, 0, {
                    'account_id': line.account_id.id,
                    'partner_id': document_result.partner_id.id,
                    'name': self.name,
                    'debit': line.tax_amount,
                })]
        document_result['state'] = 'posted'

    def create_import_stock_move(self):
        stock_move_document_information = self._prepare_import_stock_move_document()
        customs_document = self.env['stock.picking'].create(stock_move_document_information)

        for line in self.customs_line_ids:
            if line.product_id_line:
                customs_document['move_lines'] = [(0, 0, {
                    'name': line.product_id_line.name,
                    'product_uom_qty': line.product_qty_line,
                    'product_id': line.product_id_line.id,
                    'product_uom': line.product_id_line.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': line.location_destination_id_line.id,
                    'price_unit': line.unit_price_line
                })]

    def create_export_stock_move(self):
        stock_move_document_information = self._prepare_export_stock_move_document()
        customs_document = self.env['stock.picking'].create(stock_move_document_information)

        for line in self.customs_line_ids:
            if line.product_id_line:
                customs_document['move_lines'] = [(0, 0, {
                    'name': line.product_id_line.name,
                    'product_uom_qty': line.product_qty_line,
                    'product_id': line.product_id_line.id,
                    'product_uom': line.product_id_line.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': line.location_destination_id_line.id,
                    'price_unit': line.product_id_line.standard_price
                })]

    def _prepare_import_stock_move_document(self):
        self.ensure_one()
        warehouse = self.location_destination_id.warehouse_id
        return {
            'move_type': 'direct',
            'location_id': self.location_id.id,
            'location_dest_id': self.location_destination_id.id,
            'partner_id': self.partner_id.id,
            'picking_type_id': warehouse.in_type_id.id,
            'bill_related_with_inventory_move': self.related_invoice_id.id,
            'origin': self.name
        }

    def _prepare_export_stock_move_document(self):
        self.ensure_one()
        warehouse = self.location_id.warehouse_id
        return {
            'move_type': 'direct',
            'location_id': self.location_id.id,
            'location_dest_id': self.location_destination_id.id,
            'partner_id': self.partner_id.id,
            'picking_type_id': warehouse.out_type_id.id,
            'bill_related_with_inventory_move': self.related_invoice_id.id,
            'origin': self.name
        }

    def action_cancel(self):
        for doc in self:
            doc.state = 'cancel'

    def action_draft(self):
        for doc in self:
            doc.state = 'draft'

    def show_inventory_move(self):
        self.ensure_one()
        inventory_related_to_customs = self.env['stock.picking'].search([('origin', 'like', self.name)])

        action_window = {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'name': 'Delivery',
            'views': [[False, 'tree'],
                      [False, 'form']],
            'context': {'create': False},
            'domain': [['id', 'in', inventory_related_to_customs.ids]],
        }
        return action_window

    @api.depends('state')
    def _count_delivery_documents(self):
        self.ensure_one()
        self.delivery_count = 0
        if self.state != 'draft':
            self.delivery_count = self.env['stock.picking'].search_count([('origin', 'like', self.name)])

    @api.depends('state')
    def show_journal_entries(self):
        self.ensure_one()
        related_journal_moves = self.env['account.move'].search([('ref', '=', self.name)])

        action_window = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'name': 'Journal Entries',
            'views': [[False, 'tree'],
                      [False, 'form']],
            'context': {'create': False},
            'domain': [["id", "in", related_journal_moves.ids]],
        }
        return action_window

    @api.depends('state')
    def _count_journal_entries(self):
        self.ensure_one()
        self.journal_entries_count = 0
        if self.state != 'draft':
            self.journal_entries_count = self.env['account.move'].search_count([('ref', '=', self.name)])

    @api.depends('state')
    def show_landed_costs(self):
        self.ensure_one()
        related_inventory_moves = self.env['stock.picking'].search([('origin', 'like', self.name)])
        landed_cost_related_to_move = self.env['stock.landed.cost'].search(
            [('picking_ids', 'in', related_inventory_moves.ids)])

        action_window = {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.landed.cost',
            'name': 'Landed Costs',
            'views': [[False, 'tree'],
                      [False, 'form']],
            'context': {'create': False},
            'domain': [["id", "in", landed_cost_related_to_move.ids]],
        }
        return action_window

    @api.depends('state')
    def _count_landed_costs(self):
        self.ensure_one()
        self.landed_costs_count = 0
        if self.state != 'draft':
            related_inventory_moves = self.env['stock.picking'].search([('origin', 'like', self.name)])
            self.landed_costs_count = self.env['stock.landed.cost'].search_count([('picking_ids', 'in', related_inventory_moves.ids)])

    def action_create_landed_cost(self):
        inventory_related_to_customs = self.env['stock.picking'].search([('origin', 'like', self.name)])
        for doc in inventory_related_to_customs:
            if doc.state != 'done':
                raise UserError(_('Please confirm Stock Picking first!'))

        landed_cost = self.env['stock.landed.cost'].create(
            {
                'date': datetime.today(),
                'picking_ids': inventory_related_to_customs.ids,
                'vendor_bill_id': self.related_invoice_id.id,
            }
        )
        for line in self.tax_line_ids:
            if line.tax_amount > 0:
                landed_cost['cost_lines'] = [(0, 0, {
                    'name': line.tax_id.name + '-' + line.journal_id.name,
                    'price_unit': line.tax_amount,
                    'product_id': line.product_id.id,
                    'split_method': 'equal'
                })]

        action_window = {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.landed.cost',
            'name': 'Landed Cost',
            'views': [[False, 'tree'],
                      [False, 'form']],
            'context': {'create': False},
            'domain': [["id", "in", landed_cost.ids]],
        }
        return action_window

