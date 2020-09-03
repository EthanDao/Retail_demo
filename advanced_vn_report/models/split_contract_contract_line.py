# -*- coding: utf-8 -*-

from odoo import models, fields


class SplitContractContractLine(models.Model):
    _name = 'split.contract.contract.line'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)

    split_id = fields.Many2one('account.move.line.split.contract', string='Phân bổ chi phí')
    contract_id = fields.Many2one('account.contract', string='Hợp đồng')
    price = fields.Monetary(string='Giá trị phân bổ')
    related_contract_compute_direct_product_price = fields.Monetary(related='contract_id.compute_direct_product_price')
    related_contract_compute_direct_employee_cost = fields.Monetary(related='contract_id.compute_direct_employee_cost')
    related_contract_compute_sale_order_amount = fields.Monetary(related='contract_id.compute_sale_order_amount')
    related_contract_fix_rate_price = fields.Monetary(related='contract_id.fix_rate_price')
