from odoo import fields, models, api
from odoo.exceptions import UserError


class AccountAssetInherit(models.Model):
    _inherit = 'account.asset'

    asset_code = fields.Char(string='Mã tài sản')
    method_period = fields.Selection([('1', 'Months'), ('12', 'Years')], string='Number of Months in a Period', default='1',
                                     help="The amount of time between two depreciations")

    def write(self, vals_list):
        asset = super(AccountAssetInherit, self).write(vals_list)
        if 'analytic_tag_ids' in vals_list and vals_list['analytic_tag_ids']:
            if self.depreciation_move_ids:
                for rec in self.depreciation_move_ids:
                    if rec.state == 'draft':
                        if rec.line_ids:
                            for line in rec.line_ids:
                                if line.debit > 0:
                                    line.analytic_tag_ids = vals_list['analytic_tag_ids']
        if 'account_analytic_id' in vals_list:
            account_analytic = self.env['account.analytic.account'].sudo().search(
                [('id', '=', vals_list['account_analytic_id'])])
            if self.depreciation_move_ids:
                for rec in self.depreciation_move_ids:
                    if rec.state == 'draft':
                        if rec.line_ids:
                            for line in rec.line_ids:
                                if line.debit > 0:
                                    line.analytic_account_id = account_analytic
        return asset

    @api.constrains('original_value')
    def check_constrains_original_value(self):
        if self.original_value:
            if self.original_value < 0:
                raise UserError("Giá trị ban đầu không thể nhỏ hơn 0.")

    @api.constrains('salvage_value')
    def check_constrains_salvage_value(self):
        if self.salvage_value and self.original_value:
            if self.salvage_value >= self.original_value:
                raise UserError("Số tiền không phân bổ phải nhỏ hơn giá trị ban đầu.")

    def unlink(self):
        for asset in self:
            if asset.state in ['open', 'paused', 'close']:
                raise UserError('Không thể xóa phân bổ này')
        return super(AccountAssetInherit, self).unlink()

    @api.onchange('asset_type')
    def _onchange_type(self):
        if self.state != 'model':
            if self.asset_type == 'sale':
                self.prorata = True
                self.method_period = '1'
