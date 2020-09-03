from odoo import fields, models, api


class ForeignCurrencyRevaluationLine (models.Model):
    _name = 'foreign.currency.revaluation.line'
    _rec_name = 'account_id'

    def _get_default_currency(self):
        usd_id = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
        if usd_id:
            return usd_id.id

    def _get_vn_currency(self):
        vnd_id = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        if vnd_id:
            return vnd_id.id

    name = fields.Char()
    revaluation_id = fields.Many2one('foreign.currency.revaluation')
    currency_id = fields.Many2one(comodel_name="res.currency", string="Tiền tệ", default=_get_default_currency)
    currency_vnd_id = fields.Many2one(comodel_name="res.currency", string="Tiền tệ", default=_get_vn_currency)
    account_id = fields.Many2one(string="Tài khoản", comodel_name="account.account")
    partner_id = fields.Many2one(string="Khách hàng", comodel_name="res.partner")
    debit = fields.Monetary(string="Nợ", currency_field="currency_id")
    debit_amount = fields.Monetary(string="Giá trị", currency_field="currency_vnd_id", group_operator="sum",)
    credit = fields.Monetary(string="Có", currency_field="currency_id")
    credit_amount = fields.Monetary(string="Giá trị", currency_field="currency_vnd_id", group_operator="sum",)
    balance_changed = fields.Monetary(string="Giá trị thay đổi", currency_field="currency_vnd_id", group_operator="sum", compute='_compute_balance_changed')

    def _compute_balance_changed(self):
        for rec in self:
            rec.balance_changed = 0
            amount = 0
            if rec.partner_id:
                if rec.account_id.internal_type == 'receivable':
                    if rec.debit_amount > 0:
                        amount = rec.debit * rec.revaluation_id.buy_rate - rec.debit_amount
                    elif rec.credit_amount > 0:
                        amount = -(rec.credit * rec.revaluation_id.buy_rate - rec.credit_amount)
                elif rec.account_id.internal_type == 'payable':
                    if rec.debit_amount > 0:
                        amount = rec.debit * rec.revaluation_id.sell_rate - rec.debit_amount
                    elif rec.credit_amount > 0:
                        amount = -(rec.credit * rec.revaluation_id.sell_rate - rec.credit_amount)
            else:
                if rec.debit_amount > 0:
                    amount = rec.debit * rec.revaluation_id.buy_rate - rec.debit_amount
                elif rec.credit_amount > 0:
                    amount = -(rec.credit * rec.revaluation_id.buy_rate - rec.credit_amount)
            rec.balance_changed = amount





