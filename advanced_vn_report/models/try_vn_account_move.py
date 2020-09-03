from odoo import fields, models


class TryVietNamAccountMove(models.Model):
    _name = 'try.vn.account.move'

    name = fields.Char()
    ref = fields.Char()
    debit_code = fields.Char()
    credit_code = fields.Char()
    amount = fields.Char()
    date = fields.Date()
    is_updated = fields.Boolean()

    def create_account_move(self):
        code_need_to_create = []
        for rec in self:
            debit_account = None
            credit_account = None
            debit_account = self.env['account.account'].search([('code', '=', rec.debit_code)])
            credit_account = self.env['account.account'].search([('code', '=', rec.credit_code)])
            # if not debit_account:
            #     if rec.debit_code not in code_need_to_create:
            #         code_need_to_create.append(rec.debit_code)
            # if not credit_account:
            #     if rec.credit_code not in code_need_to_create:
            #         code_need_to_create.append(rec.credit_code)

            new_account_move = self.env['account.move'].sudo().create({
                'ref': rec.name + '|' + rec.ref,
                'date': rec.date,
                'line_ids': [
                    [0, 0, {
                        "account_id": debit_account.id,
                        "related_account_id": credit_account.id,
                        "company_currency_id": 23,
                        "debit": rec.amount,
                        "credit": 0
                    }],
                    [0, 0, {
                        "account_id": credit_account.id,
                        "related_account_id": debit_account.id,
                        "company_currency_id": 23,
                        "debit": 0,
                        "credit": rec.amount
                    }]
                ]
            })
            new_account_move.post()
