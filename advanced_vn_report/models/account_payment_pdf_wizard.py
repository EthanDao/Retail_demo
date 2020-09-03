# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPaymentPDFWizard(models.Model):
    _name = 'account.payment.pdf.wizard'

    account_payment_id = fields.Many2one('account.payment')
    new_description = fields.Text('Description')
    address = fields.Char('Địa chỉ')

    def action_print_pdf(self):
        self.account_payment_id.latest_address = self.address
        self.account_payment_id.latest_description = self.new_description
        return {
            'type': 'ir.actions.act_url',
            'name': "Print PDF",
            'target': 'new',
            'url': '/report/pdf/account.payment'
        }
        # return self.env.ref('advanced_account.action_payment_pdf_export').report_action(self.account_payment_id)
