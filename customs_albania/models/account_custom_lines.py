from odoo import models, fields, api


class CustomsLinesCP(models.Model):
    _name = 'account.customs.line'

    customs_id = fields.Many2one('account.customs', string='Customs Entry',
                                 index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",
                                 check_company=True,
                                 help="The move of this entry line.")

    sequence = fields.Integer(string='Sequence', default=10)

    partner_id_line = fields.Many2one('res.partner', string="Partner")
    product_id_line = fields.Many2one('product.product', string="Product", required=True)

    location_id_line = fields.Many2one('stock.location', string="Location")
    location_destination_id_line = fields.Many2one('stock.location', string="Destination Location")
    unit_price_line = fields.Float(string="Price")
    product_qty_line = fields.Float(string="Quantity")
    total_line = fields.Float(string="Total", compute='_get_line_total')

    def _get_line_total(self):
        for line in self:
            line.total_line = line.unit_price_line * line.product_qty_line

    @api.onchange('sequence')
    def _default_locations_id_line(self):
        self.partner_id_line = self.customs_id.partner_id.id
        self.location_id_line = self.customs_id.location_id.id
        self.location_destination_id_line = self.customs_id.location_destination_id.id