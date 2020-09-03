from datetime import date

from odoo import fields, models


class ForeignCurrencyRevaluation(models.Model):
    _name = 'foreign.currency.revaluation'

    def _get_default_currency(self):
        usd_id = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
        if usd_id:
            return usd_id.id

    def _get_default_rate(self):
        vnd_id = self.env.company.currency_id
        if vnd_id:
            return vnd_id._get_rates(company=self.env.company, date=date.today())[vnd_id.id]

    name = fields.Char()
    date_to = fields.Date(string="Đến ngày", default=fields.date.today())
    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)
    buy_rate = fields.Monetary(string="Tỷ giá mua", currency_field="company_currency_id", default=_get_default_rate)
    sell_rate = fields.Monetary(string="Tỷ giá bán", currency_field="company_currency_id", default=_get_default_rate)
    line_ids = fields.One2many('foreign.currency.revaluation.line', 'revaluation_id', string='Danh sách')
    currency_id = fields.Many2one(comodel_name="res.currency", string="Ngoại tệ (USD)", default=_get_default_currency)
    count_account_move = fields.Integer('Bút toán liên quan', compute='compute_count_account_move')
    count_account_move_posted = fields.Integer('Bút toán liên quan', compute='compute_count_account_move_posted')
    state = fields.Selection(
        [('draft', 'Mới'), ('revaluated', 'Đã đánh giá'), ('posted', 'Xong')],
        'Trạng thái', readonly=True, copy=False, default='draft')

    def compute_count_account_move(self):
        for rec in self:
            rec.count_account_move = 0
            rec.count_account_move = rec.env['account.move'].sudo().search_count(
                [('foreign_currency_revaluation_id', '=', self.id),
                 ('foreign_currency_revaluation_bool', '=', False)])

    def action_view_account_move(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('foreign_currency_revaluation_id', '=', self.id),
                            ('foreign_currency_revaluation_bool', '=', False)]
        return action

    def compute_count_account_move_posted(self):
        for rec in self:
            rec.count_account_move_posted = 0
            rec.count_account_move_posted = rec.env['account.move'].sudo().search_count(
                [('foreign_currency_revaluation_id', '=', self.id),
                 ('foreign_currency_revaluation_bool', '=', True)])

    def action_view_account_move_posted(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('foreign_currency_revaluation_id', '=', self.id),
                            ('foreign_currency_revaluation_bool', '=', True)]
        return action

    def load_data(self):
        date_to = self.date_to
        curency = self.currency_id.id
        ## các tài khoản bình thường
        # tim account sum # 0
        self._cr.execute('''SELECT line.account_id, SUM(line.balance)
                                           FROM account_move_line line
                                           WHERE line.date <= %s AND line.parent_state = 'posted' AND line.account_id IN (SELECT id FROM account_account WHERE internal_type NOT IN ('receivable', 'payable'))
                                           GROUP BY line.account_id having SUM(line.balance) < 0.1
                                       ''', (date_to,))
        balance_account = self.env.cr.fetchall()
        balance_account_ids = []
        for e in balance_account:
            balance_account_ids.append(e[0])
        if len(balance_account_ids) > 0:
            self._cr.execute('''SELECT line.account_id, SUM(line.amount_currency), SUM(line.balance)
                                       FROM account_move_line line
                                       WHERE line.date <= %s AND line.parent_state = 'posted' AND line.account_id IN (SELECT id FROM account_account WHERE internal_type NOT IN ('receivable', 'payable')) AND line.currency_id = '%s'
                                       AND line.account_id not in %s
                                       GROUP BY line.account_id
                                   ''', (date_to, curency, tuple(balance_account_ids)))
        else:
            self._cr.execute('''SELECT line.account_id, SUM(line.amount_currency), SUM(line.balance)
                                                   FROM account_move_line line
                                                   WHERE line.date <= %s AND line.parent_state = 'posted' AND line.account_id IN (SELECT id FROM account_account WHERE internal_type NOT IN ('receivable', 'payable')) AND line.currency_id = '%s'
                                                   GROUP BY line.account_id
                                               ''', (date_to, curency,))
        result = self.env.cr.fetchall()
        ## các tài khoản lưỡng tính (nhóm theo khách hàng)
        if len(balance_account_ids) > 0:
            self._cr.execute('''SELECT line.account_id, line.partner_id, SUM(line.amount_currency), SUM(line.balance)
                                               FROM account_move_line line
                                               WHERE line.date <= %s AND line.parent_state = 'posted' AND line.account_id IN (SELECT id FROM account_account WHERE internal_type IN ('receivable', 'payable')) AND line.currency_id = '%s'
                                               AND line.account_id not in %s
                                               GROUP BY line.account_id,line.partner_id
                                           ''', (date_to, curency, tuple(balance_account_ids)))
        else:
            self._cr.execute('''SELECT line.account_id, line.partner_id, SUM(line.amount_currency), SUM(line.balance)
                                                           FROM account_move_line line
                                                           WHERE line.date <= %s AND line.parent_state = 'posted' AND line.account_id IN (SELECT id FROM account_account WHERE internal_type IN ('receivable', 'payable')) AND line.currency_id = '%s'
                                                           GROUP BY line.account_id,line.partner_id
                                                       ''', (date_to, curency,))
        result2 = self.env.cr.fetchall()
        list = []
        for res in result:
            if res[1]:
                if res[1] > 0:
                    data = {
                        'account_id': res[0],
                        'debit': res[1],
                        'debit_amount': res[2],
                    }
                    list.append(data)
                elif res[1] < 0:
                    data = {
                        'account_id': res[0],
                        'credit': abs(res[1]),
                        'credit_amount': abs(res[2]),
                    }
                    list.append(data)
        for res in result2:
            if res[2]:
                if res[2] > 0:
                    data = {
                        'account_id': res[0],
                        'partner_id': res[1],
                        'debit': res[2],
                        'debit_amount': res[3],
                    }
                    list.append(data)
                elif res[2] < 0:
                    data = {
                        'account_id': res[0],
                        'partner_id': res[1],
                        'credit': abs(res[2]),
                        'credit_amount': abs(res[3]),
                    }
                    list.append(data)
        self.line_ids.sudo().unlink()
        self.sudo().line_ids = [(5, 0, 0)] + [(0, 0, l) for l in list]
        return

    def confirm(self):
        if self.line_ids:
            account_413 = self.env['account.account'].sudo().search([('code', '=', '413')]).id
            for line in self.line_ids:
                account_move_lines = []
                if line.partner_id:
                    amount = 0
                    if line.account_id.internal_type == 'receivable':
                        if line.debit_amount > 0:
                            amount = line.debit * self.buy_rate - line.debit_amount
                        elif line.credit_amount > 0:
                            amount = -(line.credit * self.buy_rate - line.credit_amount)
                    elif line.account_id.internal_type == 'payable':
                        if line.debit_amount > 0:
                            amount = line.debit * self.sell_rate - line.debit_amount
                        elif line.credit_amount > 0:
                            amount = -(line.credit * self.sell_rate - line.credit_amount)
                    if amount > 0:
                        debit_line = {
                            'account_id': line.account_id.id,
                            'name': self.name,
                            'debit': amount,
                            'amount_currency': 0,
                            'partner_id': line.partner_id.id,
                            'currency_id': self.currency_id.id,
                        }
                        credit_line = {
                            'account_id': account_413,
                            'name': self.name,
                            'credit': amount,
                            'amount_currency': 0,
                            'partner_id': line.partner_id.id,
                            'currency_id': self.currency_id.id,
                        }
                        account_move_lines.append(debit_line)
                        account_move_lines.append(credit_line)
                    elif amount < 0:
                        debit_line = {
                            'account_id': account_413,
                            'name': self.name,
                            'debit': abs(amount),
                            'amount_currency': 0,
                            'partner_id': line.partner_id.id,
                            'currency_id': self.currency_id.id,
                        }
                        credit_line = {
                            'account_id': line.account_id.id,
                            'name': self.name,
                            'credit': abs(amount),
                            'amount_currency': 0,
                            'partner_id': line.partner_id.id,
                            'currency_id': self.currency_id.id,
                        }
                        account_move_lines.append(debit_line)
                        account_move_lines.append(credit_line)
                else:
                    amount = 0
                    if line.debit_amount > 0:
                        amount = line.debit * self.buy_rate - line.debit_amount
                    elif line.credit_amount > 0:
                        amount = -(line.credit * self.buy_rate - line.credit_amount)
                    if amount > 0:
                        debit_line = {
                            'account_id': line.account_id.id,
                            'name': self.name,
                            'debit': amount,
                            'amount_currency': 0,
                            'currency_id': self.currency_id.id,
                        }
                        credit_line = {
                            'account_id': account_413,
                            'name': self.name,
                            'credit': amount,
                            'amount_currency': 0,
                            'currency_id': self.currency_id.id,
                        }
                        account_move_lines.append(debit_line)
                        account_move_lines.append(credit_line)
                    elif amount < 0:
                        debit_line = {
                            'account_id': account_413,
                            'name': self.name,
                            'debit': abs(amount),
                            'amount_currency': 0,
                            'currency_id': self.currency_id.id,
                        }
                        credit_line = {
                            'account_id': line.account_id.id,
                            'name': self.name,
                            'credit': abs(amount),
                            'amount_currency': 0,
                            'currency_id': self.currency_id.id,
                        }
                        account_move_lines.append(debit_line)
                        account_move_lines.append(credit_line)
                if account_move_lines:
                    account_move = self.env['account.move'].sudo().create({
                        'foreign_currency_revaluation_id': self.id,
                        'ref': self.name,
                        'journal_id': self.env.ref('advanced_vn_report.revaluation_foreign_currency_journal').id,
                        'line_ids': [(0, 0, account_move_line) for account_move_line in account_move_lines]
                    })
                    account_move.sudo().action_post()
            self.load_data()
            self.state = 'revaluated'

    def finish(self):
        account_moves = self.env['account.move'].sudo().search(
            [('foreign_currency_revaluation_id', '=', self.id), ('state', '=', 'posted'),
             ('foreign_currency_revaluation_bool', '=', False)])
        account_413 = self.env['account.account'].sudo().search([('code', '=', '413')]).id
        account_635 = self.env['account.account'].sudo().search([('code', '=', '635')]).id
        account_515 = self.env['account.account'].sudo().search([('code', '=', '515')]).id
        amount = 0
        account_move_lines = []
        if account_moves:
            for account_move in account_moves:
                for line in account_move.line_ids:
                    if line.account_id.id == account_413:
                        amount += line.balance
        if amount > 0:
            debit_line = {
                'account_id': account_635,
                'name': self.name,
                'debit': amount,
            }
            credit_line = {
                'account_id': account_413,
                'name': self.name,
                'credit': amount,
            }
            account_move_lines.append(debit_line)
            account_move_lines.append(credit_line)
        elif amount < 0:
            debit_line = {
                'account_id': account_413,
                'name': self.name,
                'debit': abs(amount),
            }
            credit_line = {
                'account_id': account_515,
                'name': self.name,
                'credit': abs(amount),
            }
            account_move_lines.append(debit_line)
            account_move_lines.append(credit_line)
        if account_move_lines:
            account_move = self.env['account.move'].sudo().create({
                'foreign_currency_revaluation_id': self.id,
                'ref': self.name,
                'journal_id': self.env.ref('advanced_vn_report.revaluation_foreign_currency_journal').id,
                'foreign_currency_revaluation_bool': True,
                'line_ids': [(0, 0, account_move_line) for account_move_line in account_move_lines]
            })
            account_move.sudo().action_post()
        self.load_data()
        self.state = 'posted'
