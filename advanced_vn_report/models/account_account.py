import datetime
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = 'account.account'

    def _compute_dn_01_balance_positive(self, date_to=datetime.date.today()):
        for rec in self:
            dn_01_balance_positive = False
            query = """SELECT sum(balance) FROM vn_account_move_line WHERE account_id in %s AND date <= %s AND parent_state = 'posted';"""
            self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', rec.code + '%')]).ids), date_to))
            query_results = self.env.cr.dictfetchall()
            account_sum = 0
            if query_results and query_results[0].get('sum') != None:
                account_sum = query_results[0].get('sum')
            if account_sum > 0:
                dn_01_balance_positive = True
            # self.env.cr.execute("""update account_account set dn_01_balance_positive = %s where id=%s""", (dn_01_balance_positive, rec.id,))
            self.env.cr.execute("""update vn_account_move_line set account_id_dn_01_balance_positive = %s where account_id=%s""", (dn_01_balance_positive, rec.id,))

    def _compute_dn_01_balance_compare_positive(self, date_to=datetime.date.today()):
        for rec in self:
            dn_01_balance_compare_positive = False
            query = """SELECT sum(balance) FROM vn_account_move_line WHERE account_id in %s AND date <= %s AND parent_state = 'posted';"""
            self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', rec.code + '%')]).ids), date_to))
            query_results = self.env.cr.dictfetchall()
            account_sum = 0
            if query_results and query_results[0].get('sum') != None:
                account_sum = query_results[0].get('sum')
            if account_sum > 0:
                dn_01_balance_compare_positive = True
            rec.dn_01_balance_compare_positive = dn_01_balance_compare_positive
            # self.env.cr.execute("""update account_account set dn_01_balance_compare_positive = %s where id=%s""", (dn_01_balance_compare_positive, rec.id,))
            self.env.cr.execute("""update vn_account_move_line set account_id_dn_01_balance_compare_positive = %s where account_id=%s""", (dn_01_balance_compare_positive, rec.id,))
