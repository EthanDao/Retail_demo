from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    related_account_id = fields.Many2one('account.account', string='Related Account')
    account_contract_id = fields.Many2one('account.contract', string='Hợp đồng')
    location_id = fields.Many2one(
        'stock.location', 'Nhà kho')
    da_ket_chuyen = fields.Boolean(
        string='Da_ket_chuyen',
        default=False)
    remain_balance_stored = fields.Monetary(string='Số tiền còn lại', default=1)

    # vn_related_account_id = fields.Many2one('account.move.line', 'account_move_line_backup')

    vn_related_account = fields.Char(string='Tài khoản đối ứng', compute="_compute_vn_related_account", store=True)

    # def _compute_vn_related_account(self):
    @api.depends('move_id')
    def _compute_vn_related_account(self):
        for rec in self:
            list_account = []
            if rec.move_id:
                if rec.move_id.vn_line_ids:
                    for line in rec.move_id.vn_line_ids:
                        if len(line) > 0:
                            if line.account_id == rec.account_id:
                                list_account.append(line.related_account_id.code)
                                list_account = list(set(list_account))
            if len(list_account) > 0:
                rec.vn_related_account = ','.join(list_account)
