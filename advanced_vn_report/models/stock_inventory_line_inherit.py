from odoo import models, fields


class StockInventoryLineInherit(models.Model):
    _inherit = "stock.inventory.line"

    note = fields.Text('Ghi chú')

