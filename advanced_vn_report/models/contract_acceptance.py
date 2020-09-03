from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ContractAcceptance (models.Model):
    _name = 'contract.acceptance'
    _description = 'Nghiệm thu hợp đồng'

    name = fields.Char()
    contract_acceptance_line_ids = fields.One2many('contract.acceptance.line', 'contract_acceptance_id', string='Hợp đồng cần nghiệm thu')
    code = fields.Char(string="Mã", required=True, copy=False, default='N/A')
    date_from = fields.Date(string='Từ ngày ')
    date_to = fields.Date(string='Đến ngày')
    state = fields.Selection(
        [('draft', 'Nháp'), ('done', 'Xong')],
        'Trạng thái', readonly=True, copy=False, default='draft')
    account_move_ids = fields.One2many('account.move', 'contract_acceptance_id', string='Bút toán liên quan')
    count_move_line = fields.Integer('Bút toán liên quan', compute='compute_count_move_line')

    def compute_count_move_line(self):
        for rec in self:
            rec.count_move_line = 0
            if rec.account_move_ids:
                rec.count_move_line = len(rec.account_move_ids)

    def load_contract_acceptance_lines(self):
        date_from = self.date_from
        date_to = self.date_to
        contract_acceptance_line_list = []
        account_154 = self.env['account.account'].sudo().search([('code', '=', '154')]).id
        account_632 = self.env['account.account'].sudo().search([('code', '=', '632')]).id
        for rec in self:
            contracts = self.env['account.contract'].sudo().search(
            [('confirm_date', '>=', date_from), ('confirm_date', '<=', date_to)])
            for contract in contracts:
                if contract.remain_cost_temp > 0:
                    contract_acceptance_line = {
                        'contract_id': contract.id,
                        'related_contract_cost_temp': contract.cost_temp,
                        'account_id': account_154,
                        'related_account_id': account_632,
                        # 'price': price,
                        # 'name': 'Kết chuyển chi phí ' + line.account_move_line_id.account_id.code + ' của hợp đồng ' +
                        #         contract['name'],
                        # 'date': rec.date,
                    }
                    contract_acceptance_line_list.append(contract_acceptance_line)
            rec.contract_acceptance_line_ids = [(5, 0, 0)]
            rec.contract_acceptance_line_ids = [(0, 0, value) for value in contract_acceptance_line_list]

    def post_contract_acceptance_lines(self):
        for rec in self:
            for line in rec.contract_acceptance_line_ids:
                account_move_lines = []
                if line.price > 0:
                    debit_line = {
                        'account_id': line.account_id.id,
                        'related_account_id': line.related_account_id.id,
                        'name': self.name + ' của hợp đồng ' + line.contract_id.name,
                        'account_contract_id': line.contract_id.id,
                        'debit': line.price,
                    }
                    credit_line = {
                        'related_account_id': line.account_id.id,
                        'account_id': line.related_account_id.id,
                        'name': self.name + ' của hợp đồng ' + line.contract_id.name,
                        'account_contract_id': line.contract_id.id,
                        'credit': line.price,
                    }
                    account_move_lines.append(debit_line)
                    account_move_lines.append(credit_line)
                    if not account_move_lines:
                        pass
                    else:
                        account_move = self.env['account.move'].sudo().create({
                            'contract_acceptance_id': self.id,
                            'ref': self.name + ' của hợp đồng ' + line.contract_id.name,
                            'journal_id': self.env.ref('advanced_vn_report.contract_acceptance_journal').id,
                            'line_ids': [(0, 0, account_move_line) for account_move_line in account_move_lines]
                        })
                        account_move.action_post()
                    line.sudo().contract_id.remain_cost_temp_stored = line.sudo().contract_id.remain_cost_temp
            rec.state = 'done'

    def cancel(self):
        for rec in self:
            for move in rec.account_move_ids:
                if move.state == 'posted':
                    raise UserError(("Có một bút toán được xác nhận, không thể hủy nghiệm thu"))
            for line in rec.contract_acceptance_line_ids:
                line.sudo().contract_id.remain_cost_temp_stored = line.sudo().contract_id.remain_cost_temp
            rec.state = 'draft'

    def action_view_contract_acceptance_account_move(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('contract_acceptance_id', '=', self.id)]
        return action

    @api.model
    def create(self, vals):
        res = super(ContractAcceptance, self).create(vals)
        if res.code == _('N/A'):
            res.code = self.env['ir.sequence'].next_by_code('advanced_vn_report.contract_acceptance_sequence') or _(
                'N/A')
        return res

    def write(self, vals):
        # res = super(ContractAcceptance, self).write(vals)
        if self.state == 'done':
            raise UserError(_("Không thể sửa nghiệm thu đã chốt"))
        return super(ContractAcceptance, self).write(vals)