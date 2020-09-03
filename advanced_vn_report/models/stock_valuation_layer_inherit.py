from odoo import fields, models, api


class StockValuationInherit (models.Model):
    _inherit = 'stock.valuation.layer'
    old_price = fields.Float(string='', required=False)
    current_price = fields.Float(string='', required=False)
    is_change_standard_price = fields.Boolean(
        string='Is change standard price', default=False)
    is_change_product_category = fields.Boolean(
        string='Is change product category', default=False)
    


