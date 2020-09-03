from odoo import models, fields


class AccountFullReconcile(models.Model):
    _inherit = 'account.full.reconcile'
    is_vn_updated = fields.Boolean(default=False)

    def create(self, vals_list):
        result = super(AccountFullReconcile, self).create(vals_list)
        result.update_vn_other_income()
        return result

    def write(self, vals):
        result = super(AccountFullReconcile, self).write(vals)
        for rec in self:
            rec.update_vn_other_income()
        return result

    def update_vn_other_income(self):
        if self.exchange_move_id and not self.is_vn_updated:
            # startlogan
            self.is_vn_updated = True
            # check if has other income
            is_need_update = False
            update_type = 1
            receivable_account = None
            payable_account = None
            for line in self.exchange_move_id.line_ids:
                if (line.debit > 0 and line.account_id.user_type_id.type == 'receivable'):
                    is_need_update = True
                    update_type = 1
                    receivable_account = line.account_id
                elif (line.credit > 0 and line.account_id.user_type_id.type == 'payable'):
                    is_need_update = True
                    payable_account = line.account_id
                    update_type = 2
            # if has other income
            if is_need_update:
                # search company setting exchange_journal;
                exchange_journal = self.exchange_move_id.company_id.currency_exchange_journal_id

                # search cash/bank account
                def move_id_id(e):
                    return e.id

                all_related_move_of_reconciled = [e.move_id for e in self.reconciled_line_ids]
                all_related_move_of_reconciled.sort(reverse=True, key=move_id_id)
                cash_bank_account_id = None

                for move in all_related_move_of_reconciled:
                    if not cash_bank_account_id:
                        for line in move.line_ids:
                            if line.debit > 0 and line.account_id.user_type_id.type == 'liquidity':
                                cash_bank_account_id = line.account_id
                            if line.credit > 0 and line.account_id.user_type_id.type == 'liquidity':
                                cash_bank_account_id = line.account_id

                if update_type == 1:
                    # find old income_amount, old_payment_amount
                    old_exchange_amount = self.exchange_move_id.line_ids.filtered(lambda line: line.debit > 0)[0].debit
                    # update bank/cash move
                    is_bank_cash_move_updated = False
                    for move in all_related_move_of_reconciled:
                        if not is_bank_cash_move_updated:
                            for line in move.line_ids:
                                if line.debit > 0 and line.account_id.user_type_id.type == 'liquidity':
                                    is_bank_cash_move_updated = True
                                    # update whole move
                                    amount_total_signed = 0
                                    for move_item in line.move_id.line_ids:
                                        if move_item.debit > 0:
                                            amount_total_signed = move_item.debit - old_exchange_amount
                                            self.env.cr.execute('update account_move_line set debit = %s where id=%s', (move_item.debit - old_exchange_amount, move_item.id,))
                                            self.env.cr.execute('update account_move_line set balance = %s where id=%s', (move_item.balance - old_exchange_amount, move_item.id,))
                                            # move_item.debit = move_item.debit - old_exchange_amount
                                            # move_item.balance = move_item.balance - old_exchange_amount
                                        else:
                                            self.env.cr.execute('update account_move_line set credit = %s where id=%s', (move_item.credit - old_exchange_amount, move_item.id,))
                                            self.env.cr.execute('update account_move_line set balance = %s where id=%s', (move_item.balance + old_exchange_amount, move_item.id,))
                                            # move_item.credit = move_item.credit + old_exchange_amount
                                            # move_item.balance = move_item.balance + old_exchange_amount
                                    self.env.cr.execute('update account_move set amount_total_signed = %s where id=%s', (amount_total_signed, line.move_id.id,))
                                    # update vn_account_move_line
                                    line.move_id.create_vn_account_move_line()

                    # update existing exchange_move_id debit account to cash/bank
                    for line in self.exchange_move_id.line_ids:
                        if line.debit > 0:
                            self.env.cr.execute('update account_move_line set account_id = %s where id=%s', (cash_bank_account_id.id, line.id,))
                            # line.account_id = cash_bank_account_id.id
                    # update vn_account_move_line
                    self.exchange_move_id.create_vn_account_move_line()
                if update_type == 2:
                    # find old income_amount, old_payment_amount
                    old_exchange_amount = self.exchange_move_id.line_ids.filtered(lambda line: line.debit > 0)[0].debit
                    # update bank/cash move
                    is_bank_cash_move_updated = False
                    for move in all_related_move_of_reconciled:
                        if not is_bank_cash_move_updated:
                            for line in move.line_ids:
                                if line.credit > 0 and line.account_id.user_type_id.type == 'liquidity':
                                    is_bank_cash_move_updated = True
                                    # update whole move
                                    amount_total_signed = 0
                                    for move_item in line.move_id.line_ids:
                                        if move_item.debit > 0:
                                            amount_total_signed = move_item.debit - old_exchange_amount
                                            self.env.cr.execute('update account_move_line set debit = %s where id=%s', (move_item.debit - old_exchange_amount, move_item.id,))
                                            self.env.cr.execute('update account_move_line set balance = %s where id=%s', (move_item.balance - old_exchange_amount, move_item.id,))
                                            # move_item.debit = move_item.debit - old_exchange_amount
                                            # move_item.balance = move_item.balance - old_exchange_amount
                                        else:
                                            self.env.cr.execute('update account_move_line set credit = %s where id=%s', (move_item.credit - old_exchange_amount, move_item.id,))
                                            self.env.cr.execute('update account_move_line set balance = %s where id=%s', (move_item.balance + old_exchange_amount, move_item.id,))
                                            # move_item.credit = move_item.credit + old_exchange_amount
                                            # move_item.balance = move_item.balance + old_exchange_amount
                                    self.env.cr.execute('update account_move set amount_total_signed = %s where id=%s', (amount_total_signed, line.move_id.id,))
                                    # update vn_account_move_line
                                    line.move_id.create_vn_account_move_line()

                    # update existing exchange_move_id debit account to cash/bank
                    for line in self.exchange_move_id.line_ids:
                        if line.credit > 0:
                            self.env.cr.execute('update account_move_line set account_id = %s where id=%s', (cash_bank_account_id.id, line.id,))
                            # line.account_id = cash_bank_account_id.id
                    # update vn_account_move_line
                    self.exchange_move_id.create_vn_account_move_line()
                # endlogan
