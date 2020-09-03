from odoo import models, api, _, _lt, fields
from odoo.tools.misc import format_date
from datetime import timedelta


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    # So cai doi tac
    # Over-ride add more columns
    def _get_columns_name(self, options):
        # sh@dowalker
        columns = [
            {},
            {'name': _('JRNL')},
            {'name': _('Account')},
            {'name': _('Ref')},
            {'name': _('Due Date'), 'class': 'date'},
            {'name': _('Matching Number')},
            {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'}]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})

        columns.append({'name': _('Balance'), 'class': 'number'})
        columns.append({'name': _('Remaining (Days)')},)
        return columns

    @api.model
    def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
        if aml['payment_id']:
            caret_type = 'account.payment'
        elif aml['move_type'] in ('in_refund', 'in_invoice', 'in_receipt'):
            caret_type = 'account.invoice.in'
        elif aml['move_type'] in ('out_refund', 'out_invoice', 'out_receipt'):
            caret_type = 'account.invoice.out'
        else:
            caret_type = 'account.move'

        date_maturity = aml['date_maturity'] and format_date(self.env, fields.Date.from_string(aml['date_maturity']))
        if aml['date_maturity']:
            now = fields.Datetime.now().date()
            remain = (aml['date_maturity'] - now).days
        else:
            remain = ''
        columns = [
            {'name': aml['journal_code']},
            {'name': aml['account_code']},
            {'name': self._format_aml_name(aml['name'], aml['ref'], aml['move_name'])},

            {'name': date_maturity or '', 'class': 'date'},
            {'name': aml['full_rec_name'] or ''},
            {'name': self.format_value(cumulated_init_balance), 'class': 'number'},
            {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
        ]
        # print(date_maturity)
        # print(aml['date_maturity'])
        if self.user_has_groups('base.group_multi_currency'):
            if aml['currency_id']:
                currency = self.env['res.currency'].browse(aml['currency_id'])
                formatted_amount = self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True)
                columns.append({'name': formatted_amount, 'class': 'number'})
            else:
                columns.append({'name': ''})
        columns.append({'name': self.format_value(cumulated_balance), 'class': 'number'})
        columns.append({'name': str(remain) or ''})
        return {
            'id': aml['id'],
            'parent_id': 'partner_%s' % partner.id,
            'name': format_date(self.env, aml['date']),
            'class': 'date',
            'columns': columns,
            'caret_options': caret_type,
            'level': 4,
        }


class ReportPartnerLedger141(models.AbstractModel):
    _inherit = "account.partner.ledger"
    _name = "account.partner.ledger.141"

    filter_account_type = [
        {'id': 'receivable', 'name': _lt('Receivable'), 'selected': False},
        {'id': 'payable', 'name': _lt('Payable'), 'selected': False},
        {'id': 'other', 'name': _lt('Regular'), 'selected': True},
        {'id': 'liquidity', 'name': _lt('Liquidity'), 'selected': False},
    ]

    @api.model
    def _get_options_domain(self, options):
        # OVERRIDE
        # Handle filter_unreconciled + filter_account_type
        domain = super(ReportPartnerLedger141, self)._get_options_domain(options)
        i = 0
        for item in domain:
            i += 1
            if 'account_id.internal_type' in item:
                domain[i - 1] = ('account_id.internal_type', 'in', ['receivable', 'payable', 'other', 'liquidity'])
            # if 'partner_id' in item:
            #     domain[i - 1] = ('|','partner_id', '!=', False,'partner_id', '=', False)
        domain.append(('account_id.code', '=', '141'))
        # Partner must be set.
        return domain

    @api.model
    def _get_templates(self):
        templates = super(ReportPartnerLedger141, self)._get_templates()
        templates['line_template'] = 'advanced_vn_report.line_template_partner_ledger_report_141'
        return templates

    @api.model
    def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
        result = super(ReportPartnerLedger141, self)._get_report_line_move_line(options, partner, aml, cumulated_init_balance, cumulated_balance)
        result['account_id'] = 141
        return result
