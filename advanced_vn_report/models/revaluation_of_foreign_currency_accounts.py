from odoo import api, fields, models
from datetime import date, datetime

from odoo.exceptions import UserError


class RevaluationOfForeignCurrencyAccounts(models.Model):
    _name = "revaluation.of.foreign.currency.accounts"
    _rec_name = "date_to"

    def _get_default_currency(self):
        usd_id = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
        if usd_id:
            return usd_id.id

    def _get_default_rate(self):
        vnd_id = self.env.company.currency_id
        if vnd_id:
            return vnd_id._get_rates(company=self.env.company, date=date.today())[vnd_id.id]

    def _get_default_account_profit(self):
        account = self.env['account.account'].sudo().search([('code', '=', '515')], limit=1)
        if account:
            return account.id

    def _get_default_account_loss(self):
        account = self.env['account.account'].sudo().search([('code', '=', '635')], limit=1)
        if account:
            return account.id

    currency_id = fields.Many2one(comodel_name="res.currency", string="Tiền tệ", default=_get_default_currency)
    date_to = fields.Date(string="Đến ngày", default=fields.date.today())
    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)
    buying_rate = fields.Monetary(string="Tỷ giá mua", currency_field="company_currency_id", default=_get_default_rate)
    sell_rate = fields.Monetary(string="Tỷ giá bán", currency_field="company_currency_id", default=_get_default_rate)

    account_profit = fields.Many2one(string="Tài khoản lãi chênh lệch tỷ giá", comodel_name="account.account", default=_get_default_account_profit)
    account_loss = fields.Many2one(string="Tài khoản lỗ chênh lệch tỷ giá", comodel_name="account.account", default=_get_default_account_loss)

    account_apply_sell_rate_need_revaluation_ids = fields.Many2many(string="Các tài khoản cần đánh giá lại (Theo tỷ giá bán)", comodel_name="account.account", relation="revaluation_account_account_sell_rate")
    account_apply_buy_rate_need_revaluation_ids = fields.Many2many(string="Các tài khoản cần đánh giá lại (Theo tỷ giá mua)", comodel_name="account.account", relation="revaluation_account_account_buy_rate")
    count_account_move = fields.Integer(string="Bút toán liên quan", compute='_compute_count_account_move')

    state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirm')], string="Trạng thái")
    account_suggest_ids = fields.Many2many(string="Gợi ý các tài khoản cần định giá", comodel_name="account.account", compute="_compute_account_suggest_ids")

    @api.depends('currency_id', 'date_to')
    def _compute_account_suggest_ids(self):
        for rec in self:
            account_ids = self.env['account.account'].sudo().search([])
            rec.account_suggest_ids = account_ids
            if rec.currency_id and rec.date_to:
                account_move_line_ids = self.env['account.move.line'].sudo().search([('parent_state', '=', 'posted'), ('currency_id', '=', self.currency_id.id), ('amount_currency', '!=', 0), ('date', '<=', self.date_to)])
                if account_move_line_ids:
                    list_account_account = []
                    for line in account_move_line_ids:
                        if line.account_id.id not in list_account_account:
                            list_account_account.append(line.account_id.id)
                    rec.account_suggest_ids = [(6, 0, list_account_account)]

    def _compute_count_account_move(self):
        for rec in self:
            rec.count_account_move = 0
            account_move_ids = self.env['account.move'].sudo().search([('revaluation_of_foreign_currency_accounts_id', '=', self.id)])
            if account_move_ids:
                rec.count_account_move = len(account_move_ids)

    def open_account_move_related(self):
        account_move_ids = self.env['account.move'].sudo().search([('revaluation_of_foreign_currency_accounts_id', '=', self.id)])
        if account_move_ids:
            return {
                'name': 'Bút toán định giá lại tài khoản ngoại tệ',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'views': [(self.env.ref('account.view_move_tree').id, 'tree'), (self.env.ref('account.view_move_form').id, 'form')],
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', account_move_ids.ids)],
                'context': {'create': False},
            }

    def confirm_revaluation(self):
        if self.account_apply_buy_rate_need_revaluation_ids and self.account_apply_sell_rate_need_revaluation_ids:
            cmp = set(self.account_apply_buy_rate_need_revaluation_ids.ids) & set(self.account_apply_sell_rate_need_revaluation_ids.ids)
            if cmp:
                raise UserError("Bạn không thể chọn cùng 1 tài khoản áp dụng cả tỷ giá mua và tỷ giá bán khi định giá lại tài khoản ngoại tệ")
        line_data = []
        count = 0
        if self.account_apply_sell_rate_need_revaluation_ids:
            list_result = []
            for account in self.account_apply_sell_rate_need_revaluation_ids:
                account_move_line_ids = self.env['account.move.line'].sudo().search([('parent_state', '=', 'posted'), ('currency_id', '=', self.currency_id.id), ('account_id', '=', account.id), ('amount_currency', '!=', 0), ('date', '<=', self.date_to)])
                if account_move_line_ids:
                    for line in account_move_line_ids:
                        new_amount = abs(line.amount_currency) * self.sell_rate
                        data = [account, abs(line.amount_currency), abs(line.balance), new_amount, new_amount - abs(line.balance)]
                        # data[account,1000,23000000,23500000,500000]
                        list_result.append(data)
            if list_result:
                account_413 = self.env['account.account'].sudo().search([('code', '=', '413')], limit=1)
                if account_413:
                    for data in list_result:
                        if data[4] < 0:
                            line_data.append([0, "virtual_1034" + str(count), {
                                "account_id": data[0].id,
                                "related_account_id": account_413.id,
                                "amount_currency": 0,
                                "currency_id": data[0].currency_id.id,
                                "debit": 0,
                                "credit": abs(data[4]),
                                "tax_line_id": False,
                                "partner_id": False,
                                "name": False,
                                "analytic_account_id": False,
                                "analytic_tag_ids": [
                                    [6, False, []]
                                ],
                                "tax_ids": [
                                    [6, False, []]
                                ],
                                "date_maturity": False
                            }])
                            count += 1
                            line_data.append([0, "virtual_1035" + str(count), {
                                "account_id": account_413.id,
                                "related_account_id": data[0].id,
                                "amount_currency": 0,
                                "currency_id": account_413.currency_id.id,
                                "debit": abs(data[4]),
                                "credit": 0,
                                "tax_line_id": False,
                                "partner_id": False,
                                "name": False,
                                "analytic_account_id": False,
                                "analytic_tag_ids": [
                                    [6, False, []]
                                ],
                                "tax_ids": [
                                    [6, False, []]
                                ],
                                "date_maturity": False
                            }])
                            count += 1
                        else:
                            line_data.append([0, "virtual_1034" + str(count), {
                                "account_id": account_413.id,
                                "related_account_id": data[0].id,
                                "amount_currency": 0,
                                "currency_id": account_413.currency_id.id,
                                "debit": 0,
                                "credit": abs(data[4]),
                                "tax_line_id": False,
                                "partner_id": False,
                                "name": False,
                                "analytic_account_id": False,
                                "analytic_tag_ids": [
                                    [6, False, []]
                                ],
                                "tax_ids": [
                                    [6, False, []]
                                ],
                                "date_maturity": False
                            }])
                            count += 1
                            line_data.append([0, "virtual_1035" + str(count), {
                                "account_id": data[0].id,
                                "related_account_id": account_413.id,
                                "amount_currency": 0,
                                "currency_id": data[0].currency_id.id,
                                "debit": abs(data[4]),
                                "credit": 0,
                                "tax_line_id": False,
                                "partner_id": False,
                                "name": False,
                                "analytic_account_id": False,
                                "analytic_tag_ids": [
                                    [6, False, []]
                                ],
                                "tax_ids": [
                                    [6, False, []]
                                ],
                                "date_maturity": False
                            }])
                            count += 1
        if self.account_apply_buy_rate_need_revaluation_ids:
            list_result = []
            for account in self.account_apply_buy_rate_need_revaluation_ids:
                account_move_line_ids = self.env['account.move.line'].sudo().search([('parent_state', '=', 'posted'), ('currency_id', '=', self.currency_id.id), ('account_id', '=', account.id), ('amount_currency', '!=', 0), ('date', '<=', self.date_to)])
                if account_move_line_ids:
                    for line in account_move_line_ids:
                        new_amount = abs(line.amount_currency) * self.buying_rate
                        data = [account, abs(line.amount_currency), abs(line.balance), new_amount, new_amount - abs(line.balance)]
                        # data[account,1000,23000000,23500000,500000]
                        list_result.append(data)
            if list_result:
                account_413 = self.env['account.account'].sudo().search([('code', '=', '413')], limit=1)
                if account_413:
                    for data in list_result:
                        if data[4] < 0:
                            count += 1
                            line_data.append([0, "virtual_1034" + str(count), {
                                "account_id": data[0].id,
                                "related_account_id": account_413.id,
                                "amount_currency": 0,
                                "currency_id": data[0].currency_id.id,
                                "debit": 0,
                                "credit": abs(data[4]),
                                "tax_line_id": False,
                                "partner_id": False,
                                "name": False,
                                "analytic_account_id": False,
                                "analytic_tag_ids": [
                                    [6, False, []]
                                ],
                                "tax_ids": [
                                    [6, False, []]
                                ],
                                "date_maturity": False
                            }])
                            count += 1
                            line_data.append([0, "virtual_1035" + str(count), {
                                "account_id": account_413.id,
                                "related_account_id": data[0].id,
                                "amount_currency": 0,
                                "currency_id": account_413.currency_id.id,
                                "debit": abs(data[4]),
                                "credit": 0,
                                "tax_line_id": False,
                                "partner_id": False,
                                "name": False,
                                "analytic_account_id": False,
                                "analytic_tag_ids": [
                                    [6, False, []]
                                ],
                                "tax_ids": [
                                    [6, False, []]
                                ],
                                "date_maturity": False
                            }])

                        else:
                            count += 1
                            line_data.append([0, "virtual_1034" + str(count), {
                                "account_id": account_413.id,
                                "related_account_id": data[0].id,
                                "amount_currency": 0,
                                "currency_id": account_413.currency_id.id,
                                "debit": 0,
                                "credit": abs(data[4]),
                                "tax_line_id": False,
                                "partner_id": False,
                                "name": False,
                                "analytic_account_id": False,
                                "analytic_tag_ids": [
                                    [6, False, []]
                                ],
                                "tax_ids": [
                                    [6, False, []]
                                ],
                                "date_maturity": False
                            }])
                            count += 1
                            line_data.append([0, "virtual_1035" + str(count), {
                                "account_id": data[0].id,
                                "related_account_id": account_413.id,
                                "amount_currency": 0,
                                "currency_id": data[0].currency_id.id,
                                "debit": abs(data[4]),
                                "credit": 0,
                                "tax_line_id": False,
                                "partner_id": False,
                                "name": False,
                                "analytic_account_id": False,
                                "analytic_tag_ids": [
                                    [6, False, []]
                                ],
                                "tax_ids": [
                                    [6, False, []]
                                ],
                                "date_maturity": False
                            }])
        if len(line_data) > 0:
            journal_id = self.env['account.journal'].sudo().search([('code', '=', 'DGTKNT')], limit=1)
            self.env['account.move'].sudo().create({
                'date': self.date_to,
                'ref': "Lãi do xử lý chênh lệch tỷ giá từ đánh giá lại ngoại tệ",
                'revaluation_of_foreign_currency_accounts_id': self.id,
                'journal_id': journal_id.id,
                'line_ids': line_data
            })
