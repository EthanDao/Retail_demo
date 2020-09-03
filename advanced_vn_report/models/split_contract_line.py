# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SplitContractLine(models.Model):
    _name = 'split.contract.line'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)
    account_move_line_id = fields.Many2one('account.move.line', string='Bút toán')
    split_id = fields.Many2one('account.move.line.split.contract', string='Phân bổ chi phí')
    init_balance = fields.Monetary(string='Số tiền ban đầu', compute='_compute_balance')
    debit = fields.Monetary(string='Nợ', compute='_compute_balance')
    credit = fields.Monetary(string='Có', compute='_compute_balance')
    remain_balance = fields.Monetary(string='Số tiền còn lại', compute='_compute_remain_balance')

    split_type = fields.Selection(
        [
            ('direct_product', 'Nguyên liệu trực tiếp'),
            ('direct_account_move_line', 'Nhân công trực tiếp'),
            ('profit', 'Doanh thu'),
            ('fixed_contract_price', 'Định mức')
        ],
        string='Loại phân bổ')
    price = fields.Monetary(string='Tổng tiền sẽ phân bổ')

    @api.onchange('account_move_line_id')
    def _compute_balance(self):
        for rec in self:
            rec.init_balance = 0
            rec.debit = 0
            rec.credit = 0
            if rec.account_move_line_id:
                rec.debit = rec.account_move_line_id.debit
                rec.credit = rec.account_move_line_id.credit
                if rec.account_move_line_id.balance > 0:
                    rec.init_balance = rec.account_move_line_id.balance
                else:
                    rec.init_balance = -rec.account_move_line_id.balance

    @api.onchange('account_move_line_id')
    def _compute_remain_balance(self):
        for rec in self:
            rec.remain_balance = rec.init_balance
            lines = self.env['account.move.line.split.contract'].search([('state', '=', 'done')])
            for line in lines.line_ids:
                if rec.account_move_line_id == line.account_move_line_id:
                    rec.remain_balance -= line.price

    @api.onchange('price')
    def _onchange_price(self):
        for rec in self:
            if rec.price > rec.remain_balance:
                raise ValidationError(('Tổng tiền phân bổ phải nhỏ hơn hoặc bằng số tiền còn lại'))
