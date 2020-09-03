# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class AccountMoveLineSplitContract(models.Model):
    _name = 'account.move.line.split.contract'

    name = fields.Char(string='Tên')
    code = fields.Char(string="Mã", required=True, copy=False, default='N/A')
    state = fields.Selection(
        [('draft', 'Mới'), ('done', 'Xong')],
        'Trạng thái', readonly=True, copy=False, default='draft')
    line_ids = fields.One2many('split.contract.line', 'split_id', string='Chi phí phân bổ')
    contract_ids = fields.One2many('split.contract.contract.line', 'split_id', string='Danh sách hợp đồng')
    transaction_entry_ids = fields.One2many('transaction.entry', 'split_id', string='Danh sách kết chuyển hợp đồng', ondelete="cascade")
    date = fields.Date(string='Ngày phân bổ', required=False)
    # @api.onchange('line_ids', 'contract_ids')
    def compute_contract_price_by_split_type(self):
        for rec in self:
            if rec.line_ids and rec.contract_ids:
                for line in rec.line_ids:
                    if line.price > line.remain_balance:
                        raise UserError(_("Giá thành phân bổ vượt quá giá trị còn lại"))
                # init contract price dict
                account_154 = self.env['account.account'].sudo().search([('code', '=', '154')]).id
                contract_dict = {}
                transaction_entry_list = []
                total_direct_product_cost = 0
                total_direct_employee_cost = 0
                total_direct_cost = 0
                total_sale_order_price = 0
                total_fix_rate_price = 0
                for contract in rec.contract_ids:
                    contract_dict[contract.contract_id.id] = {
                        'price': 0,
                        'name': contract.contract_id.name,
                        'direct_product_cost': contract.contract_id.compute_direct_product_price,
                        'direct_employee_cost': contract.contract_id.compute_direct_employee_cost,
                        'direct_cost': contract.contract_id.compute_direct_product_price + contract.contract_id.compute_direct_employee_cost,
                        'sale_order_price': contract.contract_id.compute_sale_order_amount,
                        'fix_rate_price': contract.contract_id.fix_rate_price,
                        # 'sale_order_contract_id': contract.contract_id.sale_order_contract_id.id,
                        # 'partner_id': contract.contract_id.sale_order_contract_id.partner_id.id,
                    }

                    total_direct_product_cost += contract.contract_id.compute_direct_product_price
                    total_direct_employee_cost += contract.contract_id.compute_direct_employee_cost
                    total_direct_cost += contract.contract_id.compute_direct_product_price + contract.contract_id.compute_direct_employee_cost
                    total_sale_order_price += contract.contract_id.compute_sale_order_amount
                    total_fix_rate_price += contract.contract_id.fix_rate_price

                # update contract price dict
                for line in rec.line_ids:
                    # depend of direct_product_cost
                    if line.split_type == 'direct_product':
                        if total_direct_product_cost == 0:
                            raise UserError(_("Chi phí nguyên liệu trực tiếp bằng 0"))
                        for index, contract in contract_dict.items():
                            price = line.price * contract['direct_product_cost'] / total_direct_product_cost
                            contract['price'] += price
                            if price > 0:
                                transaction_entry_dict = {
                                    'contract_id': index,
                                    'account_id': line.account_move_line_id.account_id.id,
                                    'related_account_id': account_154,
                                    'price': price,
                                    'name': 'Kết chuyển chi phí ' + line.account_move_line_id.account_id.code + ' của hợp đồng ' +
                                            contract['name'],
                                    'date': rec.date,
                                    # 'sale_order_contract_id': contract['sale_order_contract_id'],
                                    'partner_id': contract['partner_id'],
                                }
                                transaction_entry_list.append(transaction_entry_dict)
                    # depend of direct_employee_cost
                    if line.split_type == 'direct_account_move_line':
                        if total_direct_employee_cost == 0:
                            raise UserError(_("Chi phí nhân công trực tiếp bằng 0"))
                        for index, contract in contract_dict.items():
                            price = line.price * contract['direct_employee_cost'] / total_direct_employee_cost
                            contract['price'] += price
                            if price > 0:
                                transaction_entry_dict = {
                                    'contract_id': index,
                                    'account_id': line.account_move_line_id.account_id.id,
                                    'related_account_id': account_154,
                                    'price': price,
                                    'name': 'Kết chuyển chi phí ' + line.account_move_line_id.account_id.code + ' của hợp đồng ' +
                                            contract['name'],
                                    'date': rec.date,
                                    # 'sale_order_contract_id': contract['sale_order_contract_id'],
                                    'partner_id': contract['partner_id'],
                                }
                                transaction_entry_list.append(transaction_entry_dict)
                    # depend of direct_product_cost + direct_employee_cost
                    if line.split_type == 'direct_product_account_move_line':
                        if total_direct_cost == 0:
                            raise UserError(_("Tổng chi phí trực tiếp bằng 0"))
                        for index, contract in contract_dict.items():
                            price = line.price * contract['direct_cost'] / total_direct_cost
                            contract['price'] += price
                            if price > 0:
                                transaction_entry_dict = {
                                    'contract_id': index,
                                    'account_id': line.account_move_line_id.account_id.id,
                                    'related_account_id': account_154,
                                    'price': price,
                                    'name': 'Kết chuyển chi phí ' + line.account_move_line_id.account_id.code + ' của hợp đồng ' +
                                            contract['name'],
                                    'date': rec.date,
                                    # 'sale_order_contract_id': contract['sale_order_contract_id'],
                                    'partner_id': contract['partner_id'],
                                }
                                transaction_entry_list.append(transaction_entry_dict)
                    # depend of sale_order_price
                    if line.split_type == 'profit':
                        if total_sale_order_price == 0:
                            raise UserError(_("Tổng doanh thu hợp đồng bằng 0"))
                        for index, contract in contract_dict.items():
                            price = line.price * contract['sale_order_price'] / total_sale_order_price
                            contract['price'] += price
                            if price > 0:
                                transaction_entry_dict = {
                                    'contract_id': index,
                                    'account_id': line.account_move_line_id.account_id.id,
                                    'related_account_id': account_154,
                                    'price': price,
                                    'name': 'Kết chuyển chi phí ' + line.account_move_line_id.account_id.code + ' của hợp đồng ' +
                                            contract['name'],
                                    'date': rec.date,
                                    # 'sale_order_contract_id': contract['sale_order_contract_id'],
                                    'partner_id': contract['partner_id'],
                                }
                                transaction_entry_list.append(transaction_entry_dict)
                    # depend of fix_rate_price
                    if line.split_type == 'fixed_contract_price':
                        if total_fix_rate_price == 0:
                            raise UserError(_("Định mức tiêu hao bằng 0"))
                        for index, contract in contract_dict.items():
                            price = line.price * contract['fix_rate_price'] / total_fix_rate_price
                            contract['price'] += price
                            if price > 0:
                                transaction_entry_dict = {
                                    'contract_id': index,
                                    'account_id': line.account_move_line_id.account_id.id,
                                    'related_account_id': account_154,
                                    'price': price,
                                    'name': 'Kết chuyển chi phí ' + line.account_move_line_id.account_id.code + ' của hợp đồng ' +
                                            contract['name'],
                                    'date': rec.date,
                                    # 'sale_order_contract_id': contract['sale_order_contract_id'],
                                    'partner_id': contract['partner_id'],
                                }
                                transaction_entry_list.append(transaction_entry_dict)
                # update real object
                for contract in rec.contract_ids:
                    contract.price = contract_dict[contract.contract_id.id]['price']
                rec.transaction_entry_ids = [(5, 0, 0)]
                rec.transaction_entry_ids = [(0, 0, value) for value in transaction_entry_list]
                # rec.transaction_entry_ids = [(6, 0, transaction_entry_list)]

    def done(self):
        for rec in self:
            rec.state = 'done'
            rec.transaction_entry_ids.update({'state': 'split'})
            for line in rec.line_ids:
                line.sudo().account_move_line_id.remain_balance_stored = line.remain_balance

    def cancel(self):
        for rec in self:
            rec.state = 'draft'
            rec.transaction_entry_ids.update({'state': 'draft'})
            for line in rec.line_ids:
                line.sudo().account_move_line_id.remain_balance_stored = line.remain_balance

    @api.onchange('line_ids', 'contract_ids')
    def onchange_line_contract_ids(self):
        for rec in self:
            line_list = []
            contract_list =[]
            for line in rec.line_ids:
                if line.account_move_line_id.id in line_list:
                    raise ValidationError(_('Dữ liệu bị trùng'))
                line_list.append(line.account_move_line_id.id)
            for contract in rec.contract_ids:
                if contract.contract_id.id in contract_list:
                    raise ValidationError(_('Dữ liệu bị trùng'))
                contract_list.append(contract.contract_id.id)

    @api.model
    def create(self, vals):
        entry = super(AccountMoveLineSplitContract, self).create(vals)
        if entry.code == _('N/A'):
            entry.code = self.env['ir.sequence'].next_by_code(
                'advanced_vn_report.account_move_line_split_contract_sequence') or _('N/A')
        return entry

    def write(self, vals):
        # res = super(TransactionEntryModel, self).write(vals)
        if self.state == 'done':
            raise UserError(_("Không thể sửa phân bổ đã chốt"))
        return super(AccountMoveLineSplitContract, self).write(vals)