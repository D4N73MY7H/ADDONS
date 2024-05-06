from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _description = 'Stock Picking'

    bill_related_with_inventory_move = fields.Many2one('account.move', store=True, string='Related Document')
    move_lines = fields.One2many('stock.move', 'picking_id', string="Stock Moves", copy=True, domain=[('product_id.detailed_type', '=', 'product')])
