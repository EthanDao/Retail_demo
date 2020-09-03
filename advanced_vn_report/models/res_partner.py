import datetime
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    related_vn_account_move_lines = fields.One2many("vn.account.move.line", 'partner_id')

    def _compute_vn_inter_balance(self, date_from=None, date_to=datetime.date.today()):

        self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_131_short_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_211_long_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_311_short_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_331_long_positive = %s""", (False,))

        self.env.cr.execute("""update vn_account_move_line set non_partner_id_balance_b01_131_short_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set non_partner_id_balance_b01_211_long_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set non_partner_id_balance_b01_311_short_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set non_partner_id_balance_b01_331_long_positive = %s""", (False,))

        # non partner 131 short
        query = """SELECT sum(balance) FROM vn_account_move_line WHERE partner_id is NULL and is_long_payment = FALSE and date_maturity_short = TRUE and account_id in %s AND date <= %s AND parent_state = 'posted';"""
        self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))
        query_results = self.env.cr.dictfetchall()
        account_sum = 0
        if query_results and query_results[0].get('sum') != None:
            account_sum = query_results[0].get('sum')
        if account_sum > 0:
            self.env.cr.execute(
                """update vn_account_move_line set non_partner_id_balance_b01_131_short_positive = TRUE where partner_id is NULL and is_long_payment = FALSE and date_maturity_short = TRUE and account_id in %s AND date <= %s AND parent_state = 'posted'; """,
                (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))

        # non partner 131 long
        query = """SELECT sum(balance) FROM vn_account_move_line WHERE partner_id is NULL and (is_long_payment = TRUE or date_maturity_short = FALSE) and account_id in %s AND date <= %s AND parent_state = 'posted';"""
        self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))
        query_results = self.env.cr.dictfetchall()
        account_sum = 0
        if query_results and query_results[0].get('sum') != None:
            account_sum = query_results[0].get('sum')
        if account_sum > 0:
            self.env.cr.execute(
                """update vn_account_move_line set non_partner_id_balance_b01_211_long_positive = TRUE where partner_id is NULL and (is_long_payment = TRUE or date_maturity_short = FALSE) and account_id in %s AND date <= %s AND parent_state = 'posted'; """,
                (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))
        # non partner 331 short
        query = """SELECT sum(balance) FROM vn_account_move_line WHERE partner_id is NULL and is_long_payment = FALSE and date_maturity_short = TRUE and account_id in %s AND date <= %s AND parent_state = 'posted';"""
        self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', '331%')]).ids), date_to))
        query_results = self.env.cr.dictfetchall()
        account_sum = 0
        if query_results and query_results[0].get('sum') != None:
            account_sum = query_results[0].get('sum')
        if account_sum > 0:
            self.env.cr.execute(
                """update vn_account_move_line set non_partner_id_balance_b01_311_short_positive = TRUE where partner_id is NULL and is_long_payment = FALSE and date_maturity_short = TRUE and account_id in %s AND date <= %s AND parent_state = 'posted'; """,
                (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))

        # non partner 331 long
        query = """SELECT sum(balance) FROM vn_account_move_line WHERE partner_id is NULL and (is_long_payment = TRUE or date_maturity_short = FALSE) and account_id in %s AND date <= %s AND parent_state = 'posted';"""
        self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', '331%')]).ids), date_to))
        query_results = self.env.cr.dictfetchall()
        account_sum = 0
        if query_results and query_results[0].get('sum') != None:
            account_sum = query_results[0].get('sum')
        if account_sum > 0:
            self.env.cr.execute(
                """update vn_account_move_line set non_partner_id_balance_b01_331_long_positive = TRUE where partner_id is NULL and (is_long_payment = TRUE or date_maturity_short = FALSE) and account_id in %s AND date <= %s AND parent_state = 'posted'; """,
                (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))

        for rec in self:
            # phai thu ngan han
            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '131') and s.date <= date_to and s.date_maturity_short and s.is_long_payment == False):
                balance += e.debit - e.credit
            if balance > 0:
                partner_id_balance_b01_131_short_positive = True
            else:
                partner_id_balance_b01_131_short_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_131_short_positive = %s where is_long_payment = FALSE and date_maturity_short = TRUE and partner_id=%s""",
                                (partner_id_balance_b01_131_short_positive, rec.id,))
            # phai thu dai han
            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '131') and s.date <= date_to and (not s.date_maturity_short or s.is_long_payment == True)):
                balance += e.debit - e.credit
            if balance > 0:
                partner_id_balance_b01_211_long_positive = True
            else:
                partner_id_balance_b01_211_long_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_211_long_positive = %s where (is_long_payment = TRUE or date_maturity_short = FALSE) and partner_id=%s""",
                                (partner_id_balance_b01_211_long_positive, rec.id,))
            # phai tra ngan han
            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '331') and s.date <= date_to and s.date_maturity_short and s.is_long_payment == False):
                balance += e.debit - e.credit
            if balance > 0:
                partner_id_balance_b01_311_short_positive = True
            else:
                partner_id_balance_b01_311_short_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_311_short_positive = %s where is_long_payment = FALSE and date_maturity_short = TRUE and partner_id=%s""",
                                (partner_id_balance_b01_311_short_positive, rec.id,))
            # phai tra dai han
            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '331') and s.date <= date_to and (not s.date_maturity_short or s.is_long_payment == True)):
                balance += e.debit - e.credit
            if balance > 0:
                partner_id_balance_b01_331_long_positive = True
            else:
                partner_id_balance_b01_331_long_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_331_long_positive = %s where (is_long_payment = TRUE or date_maturity_short = FALSE) and partner_id=%s""",
                                (partner_id_balance_b01_331_long_positive, rec.id,))

            balance_b01_136 = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: (s.account_id.code.startswith('1385') or s.account_id.code.startswith(
                        '1388') or s.account_id.code.startswith('334') or s.account_id.code.startswith(
                        '338') or s.account_id.code.startswith('141') or s.account_id.code.startswith(
                        '244')) and s.date_maturity_short and s.date <= date_to):
                balance_b01_136 += e.debit - e.credit
            if balance_b01_136 > 0:
                balance_b01_136_positive = True
            else:
                balance_b01_136_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_136_positive = %s where partner_id=%s""", (balance_b01_136_positive, rec.id,))

            balance_b01_139 = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: s.account_id.code.startswith('1381') and s.date <= date_to):
                balance_b01_139 += e.debit - e.credit
            if balance_b01_139 > 0:
                balance_b01_139_positive = True
            else:
                balance_b01_139_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_139_positive = %s where partner_id=%s""", (balance_b01_139_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '1383') and not s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_215_positive = True
            else:
                balance_b01_215_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_215_positive = %s where partner_id=%s""", (balance_b01_215_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: s.account_id.code.startswith('333') and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_153_positive = True
            else:
                balance_b01_153_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_153_positive = %s where partner_id=%s""", (balance_b01_153_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: (s.account_id.code.startswith(
                    '1385') or s.account_id.code.startswith('1388') or s.account_id.code.startswith(
                '334') or s.account_id.code.startswith('338') or s.account_id.code.startswith(
                '141') or s.account_id.code.startswith('244')) and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_216_positive = True
            else:
                balance_b01_216_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_216_positive = %s where partner_id=%s""", (balance_b01_216_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '333') and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_313_positive = True
            else:
                balance_b01_313_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_313_positive = %s where partner_id=%s""", (balance_b01_313_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '334') and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_314_positive = True
            else:
                balance_b01_314_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_314_positive = %s where partner_id=%s""", (balance_b01_314_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '3387') and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_318_positive = True
            else:
                balance_b01_318_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_318_positive = %s where partner_id=%s""", (balance_b01_318_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: (s.account_id.code.startswith(
                    '338') or s.account_id.code.startswith('138') or s.account_id.code.startswith(
                '344')) and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_319_positive = True
            else:
                balance_b01_319_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_319_positive = %s where partner_id=%s""", (balance_b01_319_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: s.account_id.code.startswith(
                        '3387') and not s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_336_positive = True
            else:
                balance_b01_336_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_336_positive = %s where partner_id=%s""", (balance_b01_336_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: (s.account_id.code.startswith('338') or s.account_id.code.startswith(
                        '334')) and not s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_337_positive = True
            else:
                balance_b01_337_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_337_positive = %s where partner_id=%s""", (balance_b01_337_positive, rec.id,))

    def _compute_vn_inter_compare_balance(self, date_from=None, date_to=datetime.date.today()):
        self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_131_short_compare_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_211_long_compare_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_311_short_compare_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_331_long_compare_positive = %s""", (False,))

        self.env.cr.execute("""update vn_account_move_line set non_partner_id_balance_b01_131_short_compare_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set non_partner_id_balance_b01_211_long_compare_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set non_partner_id_balance_b01_311_short_compare_positive = %s""", (False,))
        self.env.cr.execute("""update vn_account_move_line set non_partner_id_balance_b01_331_long_compare_positive = %s""", (False,))

        # non partner 131 short
        query = """SELECT sum(balance) FROM vn_account_move_line WHERE partner_id is NULL and is_long_payment = FALSE and date_maturity_short = TRUE and account_id in %s AND date <= %s AND parent_state = 'posted';"""
        self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))
        query_results = self.env.cr.dictfetchall()
        account_sum = 0
        if query_results and query_results[0].get('sum') != None:
            account_sum = query_results[0].get('sum')
        if account_sum > 0:
            self.env.cr.execute(
                """update vn_account_move_line set non_partner_id_balance_b01_131_short_compare_positive = TRUE where partner_id is NULL and is_long_payment = FALSE and date_maturity_short = TRUE and account_id in %s AND date <= %s AND parent_state = 'posted'; """,
                (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))

        # non partner 131 long
        query = """SELECT sum(balance) FROM vn_account_move_line WHERE partner_id is NULL and (is_long_payment = TRUE or date_maturity_short = FALSE) and account_id in %s AND date <= %s AND parent_state = 'posted';"""
        self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))
        query_results = self.env.cr.dictfetchall()
        account_sum = 0
        if query_results and query_results[0].get('sum') != None:
            account_sum = query_results[0].get('sum')
        if account_sum > 0:
            self.env.cr.execute(
                """update vn_account_move_line set non_partner_id_balance_b01_211_long_compare_positive = TRUE where partner_id is NULL and (is_long_payment = TRUE or date_maturity_short = FALSE) and account_id in %s AND date <= %s AND parent_state = 'posted'; """,
                (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))
        # non partner 331 short
        query = """SELECT sum(balance) FROM vn_account_move_line WHERE partner_id is NULL and is_long_payment = FALSE and date_maturity_short = TRUE and account_id in %s AND date <= %s AND parent_state = 'posted';"""
        self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', '331%')]).ids), date_to))
        query_results = self.env.cr.dictfetchall()
        account_sum = 0
        if query_results and query_results[0].get('sum') != None:
            account_sum = query_results[0].get('sum')
        if account_sum > 0:
            self.env.cr.execute(
                """update vn_account_move_line set non_partner_id_balance_b01_311_short_compare_positive = TRUE where partner_id is NULL and is_long_payment = FALSE and date_maturity_short = TRUE and account_id in %s AND date <= %s AND parent_state = 'posted'; """,
                (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))

        # non partner 331 long
        query = """SELECT sum(balance) FROM vn_account_move_line WHERE partner_id is NULL and (is_long_payment = TRUE or date_maturity_short = FALSE) and account_id in %s AND date <= %s AND parent_state = 'posted';"""
        self.env.cr.execute(query, (tuple(self.env['account.account'].search([('code', 'ilike', '331%')]).ids), date_to))
        query_results = self.env.cr.dictfetchall()
        account_sum = 0
        if query_results and query_results[0].get('sum') != None:
            account_sum = query_results[0].get('sum')
        if account_sum > 0:
            self.env.cr.execute(
                """update vn_account_move_line set non_partner_id_balance_b01_331_long_compare_positive = TRUE where partner_id is NULL and (is_long_payment = TRUE or date_maturity_short = FALSE) and account_id in %s AND date <= %s AND parent_state = 'posted'; """,
                (tuple(self.env['account.account'].search([('code', 'ilike', '131%')]).ids), date_to))

        for rec in self:
            # phai thu ngan han
            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '131') and s.date_maturity_short and s.date <= date_to and s.is_long_payment == False):
                balance += e.debit - e.credit
            if balance > 0:
                partner_id_balance_b01_131_short_compare_positive = True
            else:
                partner_id_balance_b01_131_short_compare_positive = False
            self.env.cr.execute(
                """update vn_account_move_line set partner_id_balance_b01_131_short_compare_positive = %s where is_long_payment = FALSE and date_maturity_short = TRUE and partner_id=%s""",
                (partner_id_balance_b01_131_short_compare_positive, rec.id,))
            # phai thu dai han
            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '131') and s.date <= date_to and (not s.date_maturity_short or s.is_long_payment == True)):
                balance += e.debit - e.credit
            if balance > 0:
                partner_id_balance_b01_211_long_compare_positive = True
            else:
                partner_id_balance_b01_211_long_compare_positive = False
            self.env.cr.execute(
                """update vn_account_move_line set partner_id_balance_b01_211_long_compare_positive = %s where (is_long_payment = TRUE or date_maturity_short = FALSE) and partner_id=%s""",
                (partner_id_balance_b01_211_long_compare_positive, rec.id,))
            # phai tra ngan han
            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '331') and s.date_maturity_short and s.date <= date_to and s.is_long_payment == False):
                balance += e.debit - e.credit
            if balance > 0:
                partner_id_balance_b01_311_short_compare_positive = True
            else:
                partner_id_balance_b01_311_short_compare_positive = False
            self.env.cr.execute(
                """update vn_account_move_line set partner_id_balance_b01_311_short_compare_positive = %s where is_long_payment = FALSE and date_maturity_short = TRUE and partner_id=%s""",
                (partner_id_balance_b01_311_short_compare_positive, rec.id,))
            # phai tra dai han
            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '331') and s.date <= date_to and (not s.date_maturity_short or s.is_long_payment == True)):
                balance += e.debit - e.credit
            if balance > 0:
                partner_id_balance_b01_331_long_compare_positive = True
            else:
                partner_id_balance_b01_331_long_compare_positive = False
            self.env.cr.execute(
                """update vn_account_move_line set partner_id_balance_b01_331_long_compare_positive = %s where (is_long_payment = TRUE or date_maturity_short = FALSE) and partner_id=%s""",
                (partner_id_balance_b01_331_long_compare_positive, rec.id,))

            balance_b01_136 = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: (s.account_id.code.startswith('1385') or s.account_id.code.startswith(
                        '1388') or s.account_id.code.startswith('334') or s.account_id.code.startswith(
                        '338') or s.account_id.code.startswith('141') or s.account_id.code.startswith(
                        '244')) and s.date_maturity_short and s.date <= date_to):
                balance_b01_136 += e.debit - e.credit
            if balance_b01_136 > 0:
                balance_b01_136_compare_positive = True
            else:
                balance_b01_136_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_136_compare_positive = %s where partner_id=%s""", (balance_b01_136_compare_positive, rec.id,))

            balance_b01_139 = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: s.account_id.code.startswith('1381') and s.date <= date_to):
                balance_b01_139 += e.debit - e.credit
            if balance_b01_139 > 0:
                balance_b01_139_compare_positive = True
            else:
                balance_b01_139_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_139_compare_positive = %s where partner_id=%s""", (balance_b01_139_compare_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '1383') and not s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_215_compare_positive = True
            else:
                balance_b01_215_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_215_compare_positive = %s where partner_id=%s""", (balance_b01_215_compare_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: s.account_id.code.startswith('333') and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_153_compare_positive = True
            else:
                balance_b01_153_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_153_compare_positive = %s where partner_id=%s""", (balance_b01_153_compare_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: (s.account_id.code.startswith(
                    '1385') or s.account_id.code.startswith('1388') or s.account_id.code.startswith(
                '334') or s.account_id.code.startswith('338') or s.account_id.code.startswith(
                '141') or s.account_id.code.startswith('244')) and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_216_compare_positive = True
            else:
                balance_b01_216_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_216_compare_positive = %s where partner_id=%s""", (balance_b01_216_compare_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '333') and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_313_compare_positive = True
            else:
                balance_b01_313_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_313_compare_positive = %s where partner_id=%s""", (balance_b01_313_compare_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '334') and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_314_compare_positive = True
            else:
                balance_b01_314_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_314_compare_positive = %s where partner_id=%s""", (balance_b01_314_compare_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: s.account_id.code.startswith(
                    '3387') and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_318_compare_positive = True
            else:
                balance_b01_318_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_318_compare_positive = %s where partner_id=%s""", (balance_b01_318_compare_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(lambda s: (s.account_id.code.startswith(
                    '338') or s.account_id.code.startswith('138') or s.account_id.code.startswith(
                '344')) and s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_319_compare_positive = True
            else:
                balance_b01_319_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_319_compare_positive = %s where partner_id=%s""", (balance_b01_319_compare_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: s.account_id.code.startswith(
                        '3387') and not s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_336_compare_positive = True
            else:
                balance_b01_336_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_336_compare_positive = %s where partner_id=%s""", (balance_b01_336_compare_positive, rec.id,))

            balance = 0
            for e in rec.related_vn_account_move_lines.filtered(
                    lambda s: (s.account_id.code.startswith('338') or s.account_id.code.startswith(
                        '334')) and not s.date_maturity_short and s.date <= date_to):
                balance += e.debit - e.credit
            if balance > 0:
                balance_b01_337_compare_positive = True
            else:
                balance_b01_337_compare_positive = False
            self.env.cr.execute("""update vn_account_move_line set partner_id_balance_b01_337_compare_positive = %s where partner_id=%s""", (balance_b01_337_compare_positive, rec.id,))
