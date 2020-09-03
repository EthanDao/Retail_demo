from odoo import fields, models, api


class TransactionEntry (models.Model):
    _name = 'transaction.entry'
    _description = 'Kết chuyển chi phí hợp đồng (Phân bổ)'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id
    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)
    name = fields.Char("Diễn giải")
    contract_id = fields.Many2one('account.contract', string='Hợp đồng')
    # sale_order_contract_id = fields.Many2one('sale.order.contract', string='Hợp đồng')
    partner_id = fields.Many2one(comodel_name="res.partner", string='Khách hàng')
    related_account_id = fields.Many2one('account.account', string='Tài khoản nợ')
    account_id = fields.Many2one('account.account', string='Tài khoản có')
    price = fields.Monetary(string='Số tiền')
    split_id = fields.Many2one('account.move.line.split.contract', string='Phân bổ chi phí', ondelete="cascade")
    posted = fields.Boolean(string='Posted', default=False)
    date = fields.Date(string='Ngày phân bổ', required=False)
    state = fields.Selection(
        [('draft', 'Mới'), ('split', 'Đã phân bổ'), ('done', 'Đã kết chuyển')],
        'Trạng thái', readonly=True, copy=False, default='draft')

    # @api.onchange('contract_id')
    # def onchange_account_contract_id(self):
    #     for rec in self:
    #         if rec.contract_id:
    #             rec.sale_order_contract_id = self.env['sale.order.contract'].sudo().search(
    #                 [('account_contract_id', '=', rec.contract_id.id)]).id,

