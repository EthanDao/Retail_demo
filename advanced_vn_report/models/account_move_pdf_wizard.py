# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPaymentPDFWizard(models.Model):
    _name = 'account.move.pdf.wizard'

    account_move_id = fields.Many2one('account.move')
    new_description = fields.Text('Description')

    def action_print_pdf(self):
        self.account_move_id.latest_description = self.new_description
        return {
            'type': 'ir.actions.act_url',
            'name': "Print PDF",
            'target': 'new',
            'url': '/report/pdf/account.move'
        }