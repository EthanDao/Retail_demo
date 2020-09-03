from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare, float_is_zero

class TransferModelLine (models.Model):
    _inherit = 'account.transfer.model.line'

    def _get_origin_account_transfer_move_line_values(self, origin_account, amount, is_debit,
                                                      write_date):
        """
        Get values to create the move line in the origin account side for a given transfer of a given amount from origin
        account to a given destination account.
        :param origin_account: the origin account
        :param amount: the amount that is being transferred
        :type amount: float
        :param is_debit: True if the transferred amount is a debit, False if credit
        :type is_debit: bool
        :param write_date: the date to use for the move line writing
        :return: a dict containing the values to create the move line
        :rtype: dict
        """
        if self.analytic_account_ids:
            anal_accounts = ', '.join(self.analytic_account_ids.mapped('name'))
            name = _('Automatic Transfer (entries with analytic account(s): %s)') % (anal_accounts,)
        else:
            name = _('Automatic Transfer (to account %s)') % self.account_id.code
        return {
            'name': name,
            'account_id': origin_account.id,
            'date_maturity': write_date,
            'credit' if is_debit else 'debit': amount,
            'related_account_id': self.account_id.id
        }

    def _get_destination_account_transfer_move_line_values(self, origin_account, amount, is_debit,
                                                           write_date):
        """
        Get values to create the move line in the destination account side for a given transfer of a given amount from
        given origin account to destination account.
        :param origin_account: the origin account
        :param amount: the amount that is being transferred
        :type amount: float
        :param is_debit: True if the transferred amount is a debit, False if credit
        :type is_debit: bool
        :param write_date: the date to use for the move line writing
        :return: a dict containing the values to create the move line
        :rtype dict:
        """
        if self.analytic_account_ids:
            anal_accounts = ', '.join(self.analytic_account_ids.mapped('name'))
            name = _('Automatic Transfer (from account %s with analytic account(s): %s)') % (
                origin_account.code, anal_accounts)
        else:
            name = _('Automatic Transfer (%s%% from account %s)') % (self.percent, origin_account.code)
        return {
            'name': name,
            'account_id': self.account_id.id,
            'date_maturity': write_date,
            'debit' if is_debit else 'credit': amount,
            'related_account_id': origin_account.id
        }

class TransferModel(models.Model):
    _inherit = "account.transfer.model"

    def _get_non_analytics_auto_transfer_move_line_values(self, lines, start_date, end_date):
        """
        Get all values to create move lines corresponding to the transfers needed by all lines without analytic
        account for a given period. It contains the move lines concerning destination accounts and the ones concerning
        the origin accounts. This process all the origin accounts one after one.
        :param lines: the move model lines to handle
        :param start_date: the start date of the period
        :param end_date: the end date of the period
        :return: a list of dict representing the values to use to create the needed move lines
        :rtype: list
        """
        self.ensure_one()
        domain = self._get_move_lines_base_domain(start_date, end_date)
        domain.append(('analytic_account_id', 'not in', self.line_ids.mapped('analytic_account_ids.id')))
        total_balance_by_accounts = self.env['account.move.line'].read_group(domain, ['balance', 'account_id'],
                                                                             ['account_id'])

        # balance = debit - credit
        # --> balance > 0 means a debit so it should be credited on the source account
        # --> balance < 0 means a credit so it should be debited on the source account
        values_list = []
        for total_balance_account in total_balance_by_accounts:
            initial_amount = abs(total_balance_account['balance'])
            source_account_is_debit = total_balance_account['balance'] >= 0
            account_id = total_balance_account['account_id'][0]
            account = self.env['account.account'].browse(account_id)
            if not float_is_zero(initial_amount, precision_digits=9):
                # move_lines_values tra ve dict cua line transfer dich
                move_lines_values, amount_left = self._get_non_analytic_transfer_values(account, lines, end_date,
                                                                                        initial_amount,
                                                                                        source_account_is_debit)

                # the line which credit/debit the source account
                substracted_amount = initial_amount - amount_left
                source_move_line = {
                    'name': _('Automatic Transfer (-%s%%)') % self.total_percent,
                    'account_id': account_id,
                    'date_maturity': end_date,
                    'credit' if source_account_is_debit else 'debit': substracted_amount,
                    #lay gia tri account id cua move line value de them vao related account id tuong ung
                    'related_account_id': move_lines_values[0].get('account_id')
                }
                values_list += move_lines_values
                values_list.append(source_move_line)
                # values_list.append({'related_account_id': move_lines_values[0].get('account_id')})
        return values_list