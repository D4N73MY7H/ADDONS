from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'Account Move'

    create_inventory_move = fields.Boolean(string='Create Inventory Move')
    location_id = fields.Many2one(comodel_name='stock.location', string='Location')
    customs_id = fields.Boolean(string='Customs')
    secondary_currency_rate = fields.Float(string='Rate', store=True)
    delivery_count = fields.Integer(string='Delivery Count', default=0, compute='_count_delivery_documents')
    customs_count = fields.Integer(string='Customs Count', default=0, compute='_count_customs_documents')
    secondary_currency_rate = fields.Float(name='Rate', store=True)
    converted_amount_residual = fields.Monetary(string='Amount Due', store=True,
                                                currency_field='company_currency_id',
                                                compute='convert_amount_residual')

    taxes_totals = fields.Binary(
        string="Invoice Totals",
        compute='_compute_taxes_totals',
        help='Edit Tax amounts if you encounter rounding issues.',
        readonly=True,
    )

    @api.depends('state')
    def _count_delivery_documents(self):
        self.ensure_one()
        if self.state != 'draft':
            self.delivery_count = self.env['stock.picking'].search_count([('bill_related_with_inventory_move', '=', self.id)])
        else:
            self.delivery_count = 0

    @api.depends('state')
    def _count_customs_documents(self):
        self.ensure_one()
        if self.state != 'draft':
            self.customs_count = self.env['account.customs'].search_count([('related_invoice_id', '=', self.id)])
        else:
            self.customs_count = 0

    def show_documents(self, model, domain, name):
        self.ensure_one()
        related_documents = self.env[model].search(domain)
        return {
            'type': 'ir.actions.act_window',
            'res_model': model,
            'name': name,
            'views': [[False, 'tree'], [False, 'form']],
            'context': {'create': False},
            'domain': [["id", "in", related_documents.ids]],
        }

    def show_customs_document(self):
        return self.show_documents('account.customs', [('related_invoice_id', '=', self.id)], 'Customs Document')

    def show_inventory_move(self):
        self.show_documents('stock.picking', [('bill_related_with_inventory_move', '=', self.id)], 'Delivery')

    def action_post(self):
        res = super(AccountMove, self).action_post()

        if self.customs_id:
            if not self.location_id:
                raise UserError(_('Please complete the Location after checking Create Inventory Move in order to create Customs'))
            if self.move_type == "in_invoice":
                self.create_customs_document('import', 'location_destination_id')
            else:
                self.create_customs_document('export', 'location_id')
            return res
        elif not self.create_inventory_move:
            return res
        else:
            # Customer Refund Invoice
            if self.move_type == "out_refund":
                self.create_in_refund_transfer()
            # Vendor Bill
            elif self.move_type == "in_invoice":
                self.create_in_transfer()
            # Vendor Refund Bill
            elif self.move_type == "in_refund":
                self.create_out_refund_transfer()
            # Customer Invoice
            else:
                self.create_out_transfer()
        return res

    def _prepare_document(self, type, location):
        self.ensure_one()
        return {
            'move_type': type,
            'name': 'Fleta Doganore e: ' + self.name,
            'partner_id': self.partner_id.id,
            'related_invoice_id': self.id,
            location: self.location_id.id,
            'date': self.invoice_date
        }

    def create_customs_document(self, type, location):
        customs_document_information = self._prepare_document(type, location)
        customs_document = self.env['account.customs'].sudo().create(customs_document_information)

        for line in self.invoice_line_ids:
            if line.product_id.name:
                customs_document['customs_line_ids'] = [(0, 0, {
                    'partner_id_line': self.partner_id.id,
                    'product_qty_line': line.quantity,
                    'product_id_line': line.product_id.id,
                    'location_id_line': customs_document.location_id.id,
                    'location_destination_id_line': customs_document.location_destination_id.id,
                    'unit_price_line': line.price_unit * self.secondary_currency_rate
                })]

    def create_in_transfer(self):
        transfer_document_information = self._prepare_transfer_in_document(self.partner_id.property_stock_supplier.id)
        transfer = self.env['stock.picking'].create(transfer_document_information)

        for line in self.invoice_line_ids:
            if line.product_id.name:
                transfer['move_lines'] = [(0, 0, {
                    'name': line.name,
                    'product_uom_qty': line.quantity,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': transfer.location_id.id,
                    'location_dest_id': transfer.location_dest_id.id,
                    'price_unit': line.price_unit * self.secondary_currency_rate
                })]

    def _prepare_transfer_in_document(self, location):
        self.ensure_one()
        warehouse = self.location_id.warehouse_id
        return {
            'move_type': 'direct',
            'location_id': location,
            'location_dest_id': self.location_id.id,
            'partner_id': self.partner_id.id,
            'picking_type_id': warehouse.in_type_id.id,
            'bill_related_with_inventory_move': self.id
        }

    def create_in_refund_transfer(self):
        transfer_document_information = self._prepare_transfer_in_document(5)
        transfer = self.env['stock.picking'].create(transfer_document_information)

        for line in self.invoice_line_ids:
            if line.product_id.name:
                char_index = line.move_id.ref.find(':')
                reference_document_string = line.move_id.ref[char_index + 2:]
                reference_document = self.env['account.move'].search([('name', 'like', reference_document_string)])
                inventory_related_to_invoice = self.env['stock.picking'].search(
                    [('bill_related_with_inventory_move', '=', reference_document.id)])
                for product in inventory_related_to_invoice.move_ids_without_package:
                    if product.product_id == line.product_id:
                        product_returned_unit_price = product.price_unit
                    transfer['move_lines'] = [(0, 0, {
                        'name': line.name,
                        'product_uom_qty': line.quantity,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom_id.id,
                        'location_id': self.location_id.id,
                        'location_dest_id': 5,
                        'price_unit': product_returned_unit_price
                    })]

    def create_out_refund_transfer(self):
        destination_id = self.env.ref('stock.stock_location_suppliers').id

        transfer_document_information = self._prepare_transfer_out_document()
        transfer = self.env['stock.picking'].create(transfer_document_information)

        for line in self.invoice_line_ids:
            if line.product_id.name:
                transfer['move_lines'] = [(0, 0, {
                    'name': line.name,
                    'product_uom_qty': line.quantity,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': destination_id,
                    'price_unit': line.price_unit * self.secondary_currency_rate
                })]

    def _prepare_transfer_out_document(self):
        self.ensure_one()
        warehouse = self.location_id.warehouse_id
        return {
            'move_type': 'direct',
            'location_id': self.location_id.id,
            'location_dest_id': self.partner_id.property_stock_customer.id,
            'partner_id': self.partner_id.id,
            'picking_type_id': warehouse.out_type_id.id,
            'bill_related_with_inventory_move': self.id,
        }

    def create_out_transfer(self):
        transfer_document_information = self._prepare_transfer_out_document()
        transfer = self.env['stock.picking'].create(transfer_document_information)

        for line in self.invoice_line_ids:
            if line.product_id.name:
                transfer['move_lines'] = [(0, 0, {
                    'name': line.name,
                    'product_uom_qty': line.quantity,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': transfer.location_dest_id.id,
                    'price_unit': line.product_id.standard_price
                })]
    @api.depends_context('lang')
    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
    )
    def _compute_taxes_totals(self):
        """Computed field used for custom widget's rendering. Only set on invoices."""
        for move in self:
            if move.is_invoice(include_receipts=True):
                base_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
                company_currency = move.company_id.currency_id
                base_line_values_list = [line._convert_to_tax_base_line_dict() for line in base_lines]
                sign = move.direction_sign
                if move.id:
                    # The invoice is stored so we can add the early payment discount lines directly to reduce the
                    # tax amount without touching the untaxed amount.
                    base_line_values_list += [
                        {
                            **line._convert_to_tax_base_line_dict(),
                            'handle_price_include': False,
                            'quantity': 1.0,
                            'price_unit': sign * line.amount_currency,
                        }
                        for line in move.line_ids.filtered(lambda line: line.display_type == 'epd')
                    ]

                tax_lines = [
                    {**line._convert_to_tax_line_dict()}
                    for line in move.line_ids.filtered(lambda line: line.display_type == 'tax')
                ]

                is_company_currency_requested = move.currency_id != move.company_id.currency_id

                tax_totals = self.env['account.tax']._prepare_tax_totals(
                    base_line_values_list,
                    company_currency,
                    tax_lines=tax_lines,
                    is_company_currency_requested=is_company_currency_requested,
                )
                move.taxes_totals = tax_totals
                for key, value in move.taxes_totals.items():
                    if isinstance(value, (int, float)):
                        move.taxes_totals[key] *= move.secondary_currency_rate  # Multiply the keys if they are int or float with move.secondary_currency
                    if key == 'groups_by_subtotal':
                        for group in value['Untaxed Amount']:
                            group['tax_group_amount'] *= move.secondary_currency_rate
                            group['tax_group_base_amount'] *= move.secondary_currency_rate
                print(move.taxes_totals['formatted_amount_total'],"FORMATED")

                # Multiply subtotals amount
                for subtotal in move.taxes_totals['subtotals']:
                    subtotal['amount'] *= move.secondary_currency_rate
                print(move.taxes_totals,"MOVE KEYS")
                return move.taxes_totals
            else:
                # Non-invoice moves don't support that field (because of multicurrency: all lines of the invoice share the same currency)
                move.taxes_totals = None

    # Njehsimi i vlerave te fatures ne monedhe me rreshtat kontabel , vleren e account move e shumzojm me kursin e kembimit
    @api.depends('partner_id','currency_id','amount_total','amount_untaxed')
    def convert_amount_residual(self):
        for rec in self:
            rec.converted_amount_residual = rec.amount_residual * rec.secondary_currency_rate



    #Bejm krahasimin tek rate dhe marrim rekordin e fundit nese data e fatures esht me e madhe se data e kursit te vendosur.
    @api.onchange('currency_id', 'invoice_date')
    def get_second_currency_value(self):
        for rec in self:
            company = self.env.company
            if rec.currency_id != company.currency_id:
                secondary_currency_rate = self.env['res.currency.rate'].search_read([
                    ('name', '<=', rec.invoice_date),
                    ('currency_id', '=', rec.currency_id.id),
                    ('company_id', '=', company.id),
                ], order='name DESC', limit=1, fields=['inverse_company_rate'])
                if secondary_currency_rate and secondary_currency_rate[0].get('inverse_company_rate'):
                    print(secondary_currency_rate,"SEC CURRENCY RATE")
                    rec.secondary_currency_rate = secondary_currency_rate[0]['inverse_company_rate']
                else:
                    rec.secondary_currency_rate = 1.0
            else:
                rec.secondary_currency_rate = 1.0

