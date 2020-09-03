from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    account_contract_id = fields.Many2one('account.contract', string='Hợp đồng')
