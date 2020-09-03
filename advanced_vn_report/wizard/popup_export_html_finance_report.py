from odoo import models, fields, api


class PopupExportHtmlFinanceReport(models.TransientModel):
    _name = 'popup.export.html.finance.report'

    date_check_to = fields.Date(string='Tính đến')
    date_check_from = fields.Date(string='Tính từ')
    is_bao_cao_can_doi_ke_toan = fields.Boolean('Dùng cho báo cáo cân đối kế toán', default=False)
    is_bao_cao_luu_chuyen_tien_te = fields.Boolean('Dùng cho báo cáo lưu chuyển tiền tệ', default=False)

    def confirm_generate_report(self):
        if self.is_bao_cao_luu_chuyen_tien_te and not self.is_bao_cao_can_doi_ke_toan:
            list_partner = []
            read = self.env['account.move.line'].read_group([('date', '>=', self.date_check_from), ('date', '<=', self.date_check_to)], ['partner_id'], 'partner_id', lazy=False)
            if read:
                for rec in read:
                    if rec['partner_id']:
                        if rec['partner_id'][0] not in list_partner:
                            list_partner.append(rec['partner_id'][0])
            partners = self.env['res.partner'].sudo().search([('id', 'in', list_partner)])
            if partners:
                for partner in partners:
                    partner._compute_vn_inter_balance(date_from=self.date_check_from, date_to=self.date_check_to)
            action = self.env.ref('advanced_vn_report.action_account_financial_report_cash_flow_statement_b03').read()[0]
            return action
        elif self.is_bao_cao_can_doi_ke_toan and not self.is_bao_cao_luu_chuyen_tien_te:
            list_partner = []
            read = self.env['account.move.line'].read_group([('date', '<=', self.date_check_to)], ['partner_id'], 'partner_id', lazy=False)
            if read:
                for rec in read:
                    if rec['partner_id']:
                        if rec['partner_id'][0] not in list_partner:
                            list_partner.append(rec['partner_id'][0])
            partners = self.env['res.partner'].sudo().search([('id', 'in', list_partner)])
            if partners:
                for partner in partners:
                    partner._compute_vn_inter_balance(date_to=self.date_check_to)
            action = self.env.ref('advanced_vn_report.action_account_report_pnl_b01').read()[0]
            return action