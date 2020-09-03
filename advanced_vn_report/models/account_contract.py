from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountContract(models.Model):
    _name = 'account.contract'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    name = fields.Char(string='Tên hợp đồng')
    currency_id = fields.Many2one('res.currency', 'Đơn vị tiền tệ', default=_get_default_currency_id, required=True)
    # sale_order_contract_id = fields.Many2one('sale.order.contract')
    is_done = fields.Boolean(string='Đã tính giá thành')
    fix_rate_price = fields.Monetary(string='Định mức tiêu hao')

    account_move_ids = fields.One2many('account.move', 'account_contract_id', string='Hóa đơn liên quan')
    transaction_entry_ids = fields.One2many('transaction.entry', 'contract_id', string='Phân bổ liên quan')
    compute_invoice_ids = fields.One2many('account.move', string='Hóa đơn doanh thu liên quan', compute='_compute_invoice_ids')
    compute_bill_ids = fields.One2many('account.move', string='Hóa đơn chi phí liên quan', compute='_compute_bill_ids')

    account_move_line_ids = fields.One2many('account.move.line', 'account_contract_id', string='Bút toán liên quan')
    compute_account_move_line_posted_ids = fields.One2many('account.move.line', string='Bút toán liên quan (Đã chốt)', compute='_compute_account_move_line_posted_ids')
    sale_order_ids = fields.One2many('sale.order', 'account_contract_id', string='Đơn hàng liên quan')
    confirm_date = fields.Date(string='Ngày quyết toán', required=False)
    # chi phí
    init_direct_expense_price = fields.Monetary(string='Chi phí trực tiếp (Thủ công)', default=0)
    compute_direct_expense_price = fields.Monetary(string='Chi phí trực tiếp từ phát sinh', compute='_compute_direct_expense_price')
    compute_indirect_expense_price = fields.Monetary(string='Chi phí gián tiếp (phân bổ chị phí)', compute='_compute_indirect_expense_price')
    compute_indirect_expense_price_draft = fields.Monetary(string='Chi phí gián tiếp (phân bổ chị phí - Dự toán)', compute='_compute_indirect_expense_price_draft')

    cost_temp = fields.Monetary(string='Giá thành hợp đồng', compute='_compute_cost_temp')
    # liên quan đến nghiệm thu
    remain_cost_temp = fields.Monetary(string='Chi phí chưa nghiệm thu', compute='_compute_remain_cost_temp')
    remain_cost_temp_stored = fields.Monetary(default=1)
    cost_temp_draft = fields.Monetary(string='Chi phí tạm tính (Chưa chốt)', compute='_compute_cost_temp_draft')
    # final_cost = fields.Monetary(string='Giá thành chốt')

    compute_direct_product_price = fields.Monetary(string='Chi phí nguyên vật liệu trực tiếp', compute='_compute_direct_product_price')
    compute_direct_employee_cost = fields.Monetary(string='Chi phí nhân công trực tiếp', compute='_compute_direct_employee_cost')
    compute_sale_order_cost = fields.Monetary(string='Giá trị quyết toán', compute='_compute_sale_order_cost')
    compute_direct_deduction_cost = fields.Monetary(string='Chi phí giảm trừ trực tiếp', compute='_compute_direct_deduction_cost')
    # compute_pnl = fields.Monetary(string='Lợi nhuận tạm tính (P&L)', compute='_compute_pnl')
    compute_sale_order_amount = fields.Monetary(string='Doanh thu', compute='_compute_sale_order_amount')
    compute_contract_profit = fields.Monetary(string='Lợi nhuận thực tế', compute='_compute_contract_profit')
    compute_confirmed = fields.Boolean(string='', compute='_compute_confirmed', default=False, store=True)
    active = fields.Boolean(string='Active', default=True)

    def _compute_account_move_line_posted_ids(self):
        for rec in self:
            rec.compute_account_move_line_posted_ids = None
            new_list = []
            for line in rec.account_move_line_ids:
                if line.move_id.state == 'posted' and (line.account_id.code.startswith(
                        '623') or line.account_id.code.startswith('627') or line.account_id.code.startswith('622')
                or line.account_id.code.startswith('621')) and (
                not line.move_id.transaction_entry_model_id.id) and (not line.move_id.value_deduction) and (
                not line.move_id.contract_acceptance_id.id):
                    new_list.append(line.id)
            rec.compute_account_move_line_posted_ids = new_list

    def _compute_invoice_ids(self):
        for rec in self:
            rec.compute_invoice_ids = None
            new_list = []
            for account_move in rec.account_move_ids:
                if (account_move.type == 'out_invoice' or account_move.type == 'out_refund') and account_move.state == 'posted':
                    new_list.append(account_move.id)
            rec.compute_invoice_ids = new_list

    def _compute_bill_ids(self):
        for rec in self:
            rec.compute_bill_ids = None
            new_list = []
            for account_move in rec.account_move_ids:
                if (account_move.type == 'in_invoice' or account_move.type == 'in_refund') and account_move.state == 'posted':
                    new_list.append(account_move.id)
            rec.compute_bill_ids = new_list

    def _compute_cost_temp(self):
        for rec in self:
            rec.cost_temp = 0
            rec.cost_temp = rec.compute_direct_product_price + rec.compute_direct_employee_cost + rec.compute_indirect_expense_price - rec.compute_direct_deduction_cost

    def _compute_cost_temp_draft(self):
        for rec in self:
            rec.cost_temp_draft = 0
            rec.cost_temp_draft = rec.init_direct_expense_price + rec.compute_direct_expense_price + rec.compute_indirect_expense_price_draft - rec.compute_direct_deduction_cost

    # chi phí hóa đơn trực tiếp (bỏ)
    def _compute_direct_expense_price(self):
        for rec in self:
            rec.compute_direct_expense_price = 0
            if rec.account_move_ids:
                total = 0
                for invoice in rec.account_move_ids:
                    if invoice.type == 'in_invoice' and invoice.state == 'posted' and not invoice.value_deduction and not invoice.contract_acceptance_id.id:
                        total -= invoice.amount_total_signed - invoice.amount_residual_signed
                    if invoice.type == 'in_refund' and invoice.state == 'posted' and not invoice.value_deduction and not invoice.contract_acceptance_id.id:
                        total += invoice.amount_total_signed - invoice.amount_residual_signed
                rec.compute_direct_expense_price = abs(total)

    def _compute_indirect_expense_price(self):
        for rec in self:
            rec.compute_indirect_expense_price = 0
            related_split_contract = self.env['split.contract.contract.line'].search([('split_id.state', '=', 'done'), ('contract_id', '=', rec.id)])
            total = 0
            for line in related_split_contract:
                total += line.price
            rec.compute_indirect_expense_price = total

    def _compute_indirect_expense_price_draft(self):
        for rec in self:
            rec.compute_indirect_expense_price_draft = 0
            related_split_contract = self.env['split.contract.contract.line'].search([('contract_id', '=', rec.id)])
            total = 0
            for line in related_split_contract:
                total += line.price
            rec.compute_indirect_expense_price_draft = total

    def _compute_direct_product_price(self):
        for rec in self:
            rec.compute_direct_product_price = 0
            if rec.account_move_line_ids:
                total = 0
                for line in rec.account_move_line_ids:
                    if (line.move_id.state == 'posted') and (line.account_id.code.startswith(
                            '623') or line.account_id.code.startswith('627') or line.account_id.code.startswith('621')) and (not line.move_id.transaction_entry_model_id.id) and (not line.move_id.value_deduction) and (not line.move_id.contract_acceptance_id.id):
                        total += line.debit
                        total -= line.credit
                rec.compute_direct_product_price = total

    def _compute_direct_employee_cost(self):
        for rec in self:
            rec.compute_direct_employee_cost = 0
            if rec.account_move_line_ids:
                total = 0
                for line in rec.compute_account_move_line_posted_ids:
                    if line.move_id.state == 'posted' and line.account_id.code.startswith('622') and not line.move_id.value_deduction and not line.move_id.contract_acceptance_id.id:
                        total += line.debit
                        total -= line.credit
                rec.compute_direct_employee_cost = abs(total)

    def _compute_sale_order_cost(self):
        for rec in self:
            rec.compute_sale_order_cost = 0
            if rec.account_move_ids:
                total = 0
                for invoice in rec.account_move_ids:
                    if invoice.type == 'out_invoice' and invoice.state == 'posted':
                        total += invoice.amount_total_signed - invoice.amount_residual_signed
                    if invoice.type == 'out_refund' and invoice.state == 'posted':
                        total += invoice.amount_total_signed - invoice.amount_residual_signed
                rec.compute_sale_order_cost = total

    def _compute_remain_cost_temp(self):
        for rec in self:
            rec.remain_cost_temp = rec.cost_temp
            related_contract_acceptance = self.env['contract.acceptance.line'].search(
                [('contract_acceptance_id.state', '=', 'done'), ('contract_id', '=', rec.id)])
            for line in related_contract_acceptance:
                rec.remain_cost_temp -= line.price

    #compute chi phi giam tru truc tiep
    def _compute_direct_deduction_cost(self):
        for rec in self:
            rec.compute_direct_deduction_cost = 0
            if rec.account_move_line_ids:
                total = 0
                for line in rec.account_move_line_ids:
                    if line.move_id.state == 'posted' and line.move_id.value_deduction:
                        total += line.debit
                        # total -= line.credit
                rec.compute_direct_deduction_cost = abs(total)

    # def _compute_pnl(self):
    #     for rec in self:
    #         rec.compute_pnl = 0
    #         if rec.sale_order_contract_id:
    #             pnl = self.env['profit.and.loss'].sudo().search(
    #             [('mrp_bom_id.number_order.contract_id', '=', rec.sale_order_contract_id.id)])
    #             if pnl:
    #                 rec.compute_pnl = pnl.profit * pnl.rate / 100

    def _compute_sale_order_amount(self):
        for rec in self:
            rec.compute_sale_order_amount = 0
            if rec.sale_order_ids:
                for sale in rec.sale_order_ids:
                    rec.compute_sale_order_amount += sale.amount_total

    def _compute_contract_profit(self):
        for rec in self:
            rec.compute_contract_profit = 0
            rec.compute_contract_profit = rec.compute_sale_order_cost - rec.cost_temp

    @api.depends('confirm_date')
    def _compute_confirmed(self):
        for rec in self:
            rec.compute_confirmed = False
            if rec.confirm_date:
                rec.compute_confirmed = True

    def write(self, vals):
        for rec in self:
            if 'active' in vals:
                if vals['active'] == False:
                    # if rec.sale_order_contract_id.can_archive == False:
                    #     raise UserError(
                    #         "Không thể đóng gói, yêu cầu ấn nút hủy")
                    if rec.compute_indirect_expense_price > 0:
                        raise UserError(
                            "Không thể đóng gói, hợp đồng đã được phân bổ chi phí")
        res = super(AccountContract, self).write(vals)
        return res