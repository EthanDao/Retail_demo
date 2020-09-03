# -*- coding: utf-8 -*-

from num2words import num2words

from odoo import models, fields, _

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
# Since invoice amounts are unsigned, this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    computed_description = fields.Text('Lý do nộp')
    latest_description = fields.Text()
    latest_address = fields.Char()
    is_long_payment = fields.Boolean(string='Thanh toán dài hạn', default=False)

    is_liquidation_payment = fields.Boolean(string='Thanh toán thanh lý', default=False)

    def post(self):
        for rec in self:
            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    rec.is_liquidation_payment = False
                    for invoice in rec.invoice_ids:
                        if invoice:
                            if invoice.is_liquidation_invoice:
                                rec.is_liquidation_payment = True
        res = super().post()
        return res

    def action_open_pdf_wizard(self):
        form_view = self.env.ref('advanced_vn_report.account_payment_pdf_wiward_form')

        return {
            'name': _('In Phiếu'),
            'res_model': 'account.payment.pdf.wizard',
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_account_payment_id': self.id,
                'default_new_description': self.computed_description,
                'default_address': self.report_address
            }
        }

    # Start print PDF

    # Prin Date FDF
    report_pdf_date = fields.Char(compute='_compute_report_pdf_date')

    def _compute_report_pdf_date(self):
        today = fields.Date.today()
        date = today.day
        month = today.month
        year = today.year
        self.report_pdf_date = 'Ngày ' + str(date) + ' tháng ' + str(month) + ' năm ' + str(year)

    # Print Người nhận tiền
    report_person_get_money = fields.Char(compute='_compute_report_person_get_money')

    def _compute_report_person_get_money(self):
        partner_name = ''
        if self.partner_id and self.partner_id.name:
            partner_name = self.partner_id.name
        self.report_person_get_money = partner_name

    report_pdf_data_ly_do_nop = fields.Char(compute='_compute_report_pdf_data_ly_do_nop')

    def _compute_report_pdf_data_ly_do_nop(self):
        self.report_pdf_data_ly_do_nop = self.latest_description

    report_pdf_data_debit_code = fields.Char(compute='_compute_report_pdf_data_debit_code')

    def _compute_report_pdf_data_debit_code(self):
        self.report_pdf_data_debit_code = ''
        if self.move_line_ids:
            for rec in self.move_line_ids:
                if rec.debit > 0:
                    self.report_pdf_data_debit_code = str(rec.account_id.code)

    report_pdf_data_credit_code = fields.Char(compute='_compute_report_pdf_data_credit_code')

    def _compute_report_pdf_data_credit_code(self):
        self.report_pdf_data_credit_code = ''
        if self.move_line_ids:
            for rec in self.move_line_ids:
                if rec.credit > 0:
                    self.report_pdf_data_credit_code = str(rec.account_id.code)

    report_pdf_data_tien_bang_chu = fields.Char(compute='_compute_report_pdf_data_tien_bang_chu')

    def _compute_report_pdf_data_tien_bang_chu(self):
        report_pdf_data_tien_bang_chu = ''
        if self.currency_id.name == 'VND':
            report_pdf_data_tien_bang_chu = str(num2words(self.amount, lang='vi_VN').title() + " Đồng Chẵn")
        elif self.currency_id.name == 'USD':
            report_pdf_data_tien_bang_chu = str(num2words(self.amount, lang='vi_VN').title() + " Đô")
        else:
            report_pdf_data_tien_bang_chu = str(num2words(self.amount, lang='vi_VN').title())
        self.report_pdf_data_tien_bang_chu = report_pdf_data_tien_bang_chu

    total_money = fields.Char(compute='_compute_get_total_money')

    def _compute_get_total_money(self):
        if self.amount and self.amount > 0:
            money = str(self.amount).split(' ')
            self.total_money = str("{:,}".format(round(float(money[0])))) + ' ' + 'VND'
        else:
            self.total_money = str(0) + ' ' + 'VND'

    report_address = fields.Char(compute='compute_address')

    def compute_address(self):
        if self.partner_id:
            if self.partner_id.street:
                street = str(self.partner_id.street)
            else:
                street = ''
            if self.partner_id.street2:
                street2 = str(self.partner_id.street2)
            else:
                street2 = ''
            if self.partner_id.city:
                city = self.partner_id.city
            else:
                city = ''
            address = street + ' ' + street2 + ' ' + city
            self.report_address = address
        else:
            self.report_address = ''

    def write(self, vals):
        if 'is_long_payment' in vals:
            for rec in self:
                # find related vn account move line mark
                self.env.cr.execute("""update vn_account_move_line set is_long_payment = %s where payment_id=%s""", (vals['is_long_payment'], rec.id,))
        return super(AccountPaymentInherit, self).write(vals)
