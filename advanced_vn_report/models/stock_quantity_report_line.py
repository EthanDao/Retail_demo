from odoo import fields, models, api


class StockQuantityReportLine (models.Model):
    _name = 'stock.quantity.report.line'
    _description = 'Description'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id
    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)
    product_id = fields.Many2one(comodel_name='product.template', string='Tên sản phẩm', required=False)
    default_code = fields.Char(related='product_id.default_code', string='Mã sản phẩm')
    uom_id = fields.Many2one(related='product_id.uom_id', string='Đơn vị')
    product_qty_start = fields.Float(string="SL tồn đầu kì")
    product_qty_end = fields.Float(string="SL tồn cuối kì")
    product_qty_in = fields.Float(string="SL nhập trong kì")
    product_qty_out = fields.Float(string="SL xuất trong kì")
    value_start = fields.Monetary(string="Thành tiền")
    value_end = fields.Monetary(string="Thành tiền")
    value_in = fields.Monetary(string="Thành tiền")
    value_out = fields.Monetary(string="Thành tiền")
    stock_quantity_report_id = fields.Many2one('stock.quantity.report', "Dòng")

