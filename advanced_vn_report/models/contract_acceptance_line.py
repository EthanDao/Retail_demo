from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ContractAcceptanceLine (models.Model):
    _name = 'contract.acceptance.line'
    _description = 'Description'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id
    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)

    contract_id = fields.Many2one('account.contract', string='Hợp đồng', ondelete="cascade")
    related_contract_cost_temp = fields.Monetary(related='contract_id.cost_temp')
    price = fields.Monetary(string='Tổng tiền nghiệm thu')
    remain_cost_temp = fields.Monetary(related='contract_id.remain_cost_temp')
    contract_acceptance_id = fields.Many2one('contract.acceptance', string='Nghiệm thu hợp đồng')
    related_account_id = fields.Many2one('account.account', string='Tài khoản nợ')
    account_id = fields.Many2one('account.account', string='Tài khoản có')

    @api.onchange('price')
    def _onchange_price(self):
        for rec in self:
            if rec.price > rec.remain_cost_temp:
                raise ValidationError(('Tổng tiền nghiệm thu phải nhỏ hơn hoặc bằng số tiền còn lại'))
