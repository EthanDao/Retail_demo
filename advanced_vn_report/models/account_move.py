import copy
import sys
import traceback

from num2words import num2words

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # related_account_id = fields.Many2one('account.account', string='Related Account')
    account_contract_id = fields.Many2one('account.contract', string='Hợp đồng')
    # sale_order_contract_id = fields.Many2one('sale.order.contract', string='Hợp đồng')
    transaction_entry_model_id = fields.Many2one('transaction.entry.model', string='Kết chuyển')
    transaction_entry_id = fields.Many2one('transaction.entry', string='Kết chuyển (dòng)')
    revaluation_of_foreign_currency_accounts_id = fields.Many2one('revaluation.of.foreign.currency.accounts', string='Định giá lại tài khoản ngoại tệ')
    computed_description = fields.Text('Lý do nộp')
    latest_description = fields.Text()
    contract_acceptance_id = fields.Many2one('contract.acceptance', string='Nghiệm thu')
    value_deduction = fields.Boolean(string="Bút toán giảm trừ giá thành hợp đồng", default=False)
    vn_line_ids = fields.One2many('vn.account.move.line', 'move_id', string='Viet Nam Account Move Line')
    nontaxable_income_source = fields.Boolean(string="Tạo ra doanh thu không chịu thuế", default=False)
    is_liquidation_invoice = fields.Boolean(string='Là hóa đơn thanh lý')
    foreign_currency_revaluation_id = fields.Many2one('foreign.currency.revaluation',)
    foreign_currency_revaluation_bool = fields.Boolean(string="Hạch toán 413 khi đánh giá lại khoản ngoại tệ", default=False)
    # vn_related_account_id = fields.Many2one('account.move.line', 'account_move_line_backup')
    #
    # vn_related_account = fields.Char(string='Tài khoản đối ứng', compute="_compute_vn_related_account")
    #
    # # def _compute_vn_related_account(self):
    #
    # def _compute_vn_related_account(self):
    #     for rec in self:
    #         list_account = []
    #         if rec.vn_line_ids:
    #             for line in rec.vn_line_ids:
    #                 if len(line) > 0:
    #                     if line.account_move_line_backup:
    #                         if line.account_move_line_backup.account_id:
    #                             list_account.append(line.related_account_id.code)
    #                             list_account = list(set(list_account))
    #         print(list_account)
    #         if len(list_account) > 0:
    #             rec.vn_related_account = ','.join(list_account)

    def compute_vn_line_ids(self):
        for rec in self:
            rec.vn_line_ids = None
            rec.vn_line_ids = self.env['vn.account.move.line'].search([('move_id', '=', rec.id)]).ids

    # @api.onchange('account_contract_id')
    # def onchange_account_contract_id(self):
    #     for rec in self:
    #         if rec.account_contract_id:
    #             for line in rec.line_ids:
    #                 line.account_contract_id = rec.account_contract_id.id

    @api.model
    def create(self, vals):
        result = super(AccountMove, self).create(vals)
        for rec in result:
            # if rec.sale_order_contract_id:
            #     rec.account_contract_id = rec.sale_order_contract_id.account_contract_id.id
            #     for line in rec.line_ids:
            #         line.account_contract_id = rec.sale_order_contract_id.account_contract_id.id
            rec.create_vn_account_move_line()
        return result

    def write(self, vals):
        result = super(AccountMove, self).write(vals)
        # if vals.get('line_ids'):
        #     for line in self.line_ids:
        #         if not line.account_contract_id:
        #             line.account_contract_id = self.sale_order_contract_id.account_contract_id.id
        self.create_vn_account_move_line()
        return result

    # @api.onchange('sale_order_contract_id')
    # def onchange_account_contract_id(self):
    #     for rec in self:
    #         if rec.sale_order_contract_id:
    #             rec.account_contract_id = rec.sale_order_contract_id.account_contract_id.id
    #             for line in rec.line_ids:
    #                 line.account_contract_id = rec.sale_order_contract_id.account_contract_id.id

    # def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
    #     # update related account id
    #     super(AccountMove, self)._recompute_dynamic_lines(recompute_all_taxes)
    #     # check if credit == debit or not
    #     # try:
    #     need_recompute_dynamic_lines = True
    #     if len(self.line_ids) < 2:
    #         need_recompute_dynamic_lines = False
    #     if len(self.line_ids) > 1:
    #         debit_sum = 0
    #         credit_sum = 0
    #         for line in self.line_ids:
    #             if line.debit > 0:
    #                 debit_sum += line.debit
    #         for line in self.line_ids:
    #             if line.credit > 0:
    #                 credit_sum += line.credit
    #         if debit_sum != credit_sum:
    #             need_recompute_dynamic_lines = False
    #     if need_recompute_dynamic_lines:
    #         # compute final partner id
    #         final_partner_id = self.commercial_partner_id.id
    #         if not final_partner_id:
    #             for line in self.line_ids:
    #                 if line.partner_id and not final_partner_id:
    #                     final_partner_id = line.partner_id
    #
    #         debit_account = None
    #         debit_account_count = 0
    #         credit_account = None
    #         credit_account_count = 0
    #         for line in self.line_ids:
    #             if line.debit > 0:
    #                 debit_account = line.account_id.id
    #                 debit_account_count += 1
    #         for line in self.line_ids:
    #             if line.credit > 0:
    #                 credit_account = line.account_id.id
    #                 credit_account_count += 1
    #         update_related_account_type = 0
    #         if debit_account_count == 1 and self.type == 'entry':
    #             update_related_account_type = 1
    #         elif credit_account_count == 1 and self.type == 'entry':
    #             update_related_account_type = 2
    #         if self.type == 'out_invoice' or self.type == 'in_refund' or update_related_account_type == 1:
    #             for line in self.line_ids:
    #                 if line.credit > 0:
    #                     line.related_account_id = debit_account
    #             # split main debit line and assign lines
    #             exist_debit_line = self.line_ids.filtered(lambda line: line.debit > 0)
    #             if len(exist_debit_line) > 0:
    #                 # try get analytic_account_id, analytic_tag_ids
    #                 analytic_account_id = None
    #                 analytic_tag_ids = []
    #                 if exist_debit_line[0].analytic_account_id:
    #                     analytic_account_id = exist_debit_line[0].analytic_account_id.id
    #                 if exist_debit_line[0].analytic_tag_ids:
    #                     analytic_tag_ids = [(4, e._origin.id, 0) for e in exist_debit_line[0].analytic_tag_ids]
    #                 self.line_ids -= exist_debit_line
    #                 exist_credit_line = self.line_ids.filtered(lambda line: line.credit > 0)
    #                 in_draft_mode = self != self._origin
    #                 for line in exist_credit_line:
    #                     if line.exists():
    #                         create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
    #                             'account.move.line'].create
    #                         candidate = create_method({
    #                             'name': line.name,
    #                             'credit': 0.0,
    #                             'debit': line.credit,
    #                             'quantity': 1.0,
    #                             'amount_currency': -line.amount_currency,
    #                             'move_id': self.id,
    #                             'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
    #                             'account_id': debit_account,
    #                             'partner_id': final_partner_id,
    #                             'exclude_from_invoice_tab': True,
    #                             'related_account_id': line.account_id.id,
    #                             'account_internal_type': 'other',
    #                             'account_contract_id': line.account_contract_id.id,
    #                             'analytic_account_id': analytic_account_id,
    #                             'analytic_tag_ids': analytic_tag_ids,
    #                         })
    #                         if in_draft_mode:
    #                             candidate._onchange_amount_currency()
    #                             candidate._onchange_balance()
    #                         try:
    #                             self.invoice_line_ids -= candidate
    #                         except Exception as ex:
    #                             print(str(ex))
    #
    #         elif self.type == 'in_invoice' or self.type == 'out_refund' or update_related_account_type == 2:
    #             for line in self.line_ids:
    #                 if line.debit > 0:
    #                     line.related_account_id = credit_account
    #             # split main credit line and assign lines
    #             exist_credit_line = self.line_ids.filtered(lambda line: line.credit > 0)
    #             if len(exist_credit_line) > 0:
    #                 # try get analytic_account_id, analytic_tag_ids
    #                 analytic_account_id = None
    #                 analytic_tag_ids = []
    #                 if exist_credit_line[0].analytic_account_id:
    #                     analytic_account_id = exist_credit_line[0].analytic_account_id.id
    #                 if exist_credit_line[0].analytic_tag_ids:
    #                     analytic_tag_ids = [(4, e._origin.id, 0) for e in exist_credit_line[0].analytic_tag_ids]
    #
    #                 self.line_ids -= exist_credit_line
    #                 exist_debit_line = self.line_ids.filtered(lambda line: line.debit > 0)
    #                 in_draft_mode = self != self._origin
    #                 for line in exist_debit_line:
    #                     if line.exists():
    #                         create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
    #                             'account.move.line'].create
    #                         candidate = create_method({
    #                             'name': line.name,
    #                             'debit': 0.0,
    #                             'credit': line.debit,
    #                             'quantity': 1.0,
    #                             'amount_currency': -line.amount_currency,
    #                             'move_id': self.id,
    #                             'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
    #                             'account_id': credit_account,
    #                             'partner_id': final_partner_id,
    #                             'exclude_from_invoice_tab': True,
    #                             'related_account_id': line.account_id.id,
    #                             'account_internal_type': 'other',
    #                             'account_contract_id': line.account_contract_id.id,
    #                             'analytic_account_id': analytic_account_id,
    #                             'analytic_tag_ids': analytic_tag_ids,
    #                         })
    #                         if in_draft_mode:
    #                             candidate._onchange_amount_currency()
    #                             candidate._onchange_balance()
    #                         try:
    #                             self.invoice_line_ids -= candidate
    #                         except Exception as ex:
    #                             print(str(ex))
    # except Exception as ex:
    #     traceback.print_exc(None, sys.stderr)
    #     a = 0

    def force_update_related_account(self):
        for rec in self:
            line_ids = rec.line_ids
            for line in line_ids:
                if len(line.related_account_id) == 0:
                    if line.debit:
                        for cline in line_ids:
                            if cline.credit == line.debit:
                                line.related_account_id = cline.account_id
                                cline.related_account_id = line.account_id

    def action_invoice_register_payment(self):
        return self.env['account.payment'] \
            .with_context(active_ids=self.ids, active_model='account.move', active_id=self.id) \
            .action_register_payment()

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        if self.transaction_entry_id:
            raise UserError(("Bút toán đã được kết kết chuyển"))
        if self.transaction_entry_model_id:
            raise UserError(("Bút toán đã được kết kết chuyển"))
        for line in self.line_ids:
            if line.da_ket_chuyen:
                raise UserError(("Bút toán đã được kết kết chuyển"))
        return res

    # In phieu thu chi
    type_ballot = fields.Selection(
        [('thu', "thu"),
         ('chi', "chi")]
    )

    def action_open_pdf_wizard_thu(self):
        form_view = self.env.ref('advanced_vn_report.account_move_pdf_wiward_form')
        self.type_ballot = 'thu'
        return {
            'name': _('In Phiếu Thu'),
            'res_model': 'account.move.pdf.wizard',
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_account_move_id': self.id,
                'default_new_description': self.computed_description,
            }
        }

    def action_open_pdf_wizard_chi(self):
        form_view = self.env.ref('advanced_vn_report.account_move_pdf_wiward_form')
        self.type_ballot = 'chi'
        return {
            'name': _('In Phiếu Chi'),
            'res_model': 'account.move.pdf.wizard',
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_account_move_id': self.id,
                'default_new_description': self.computed_description,
            }
        }

    report_pdf_date = fields.Char(compute='_compute_report_pdf_date')

    def _compute_report_pdf_date(self):
        today = fields.Date.today()
        date = today.day
        month = today.month
        year = today.year
        self.report_pdf_date = "Ngày " + str(
            date) + " tháng " + str(month) + " năm " + str(year)

    report_pdf_data_credit_code = fields.Char(compute='_report_pdf_data_credit_code')
    report_pdf_data_debit_code = fields.Char(compute='_report_pdf_data_debit_code')

    def _report_pdf_data_credit_code(self):
        self.report_pdf_data_credit_code = ''
        if self.line_ids and len(self.line_ids) > 0:
            for rec in self.line_ids:
                if rec.credit > 0:
                    self.report_pdf_data_credit_code = str(rec.account_id.code)
                else:
                    self.report_pdf_data_credit_code = ''

    def _report_pdf_data_debit_code(self):
        self.report_pdf_data_debit_code = ''
        if self.line_ids and len(self.line_ids) > 0:
            for rec in self.line_ids:
                if rec.debit > 0:
                    self.report_pdf_data_debit_code = str(rec.account_id.code)
                else:
                    self.report_pdf_data_debit_code = ''

    report_pdf_data_tien_bang_chu = fields.Char(compute='_compute_report_pdf_data_tien_bang_chu')

    def _compute_report_pdf_data_tien_bang_chu(self):
        report_pdf_data_tien_bang_chu = ''
        if self.currency_id.name == 'VND':
            report_pdf_data_tien_bang_chu = str(
                num2words(self.amount_total_signed, lang='vi_VN').title() + " Đồng Chẵn")
        elif self.currency_id.name == 'USD':
            report_pdf_data_tien_bang_chu = str(num2words(self.amount_total_signed, lang='vi_VN').title() + " Đô")
        else:
            report_pdf_data_tien_bang_chu = str(num2words(self.amount_total_signed, lang='vi_VN').title())

        self.report_pdf_data_tien_bang_chu = report_pdf_data_tien_bang_chu

    total_money = fields.Char(compute='_compute_get_total_money')

    def _compute_get_total_money(self):
        if self.amount_total_signed and self.amount_total_signed > 0:
            money = str(self.amount_total_signed).split(' ')
            self.total_money = str("{:,}".format(round(float(money[0])))) + ' ' + 'VND'
        else:
            self.total_money = str(0) + ' ' + 'VND'

    def create_vn_account_move_line(self):
        for rec in self:
            try:
                # remove old vn.account.move.line
                self.env['vn.account.move.line'].search([('move_id', '=', rec.id)]).unlink()
                # copy and create new one

                # init date maturity
                init_date_maturity = None
                init_date_maturity_tmp = None
                count = 0
                for line in rec.line_ids.filtered(lambda line_non_display: not line_non_display.display_type):
                    if line.date_maturity:
                        init_date_maturity_tmp = line.date_maturity
                        count += 1
                if count == 1:
                    init_date_maturity = init_date_maturity_tmp
                new_vn_account_move_line = []
                for line in rec.line_ids.filtered(lambda line_non_display: not line_non_display.display_type):
                    vn_account_move_line_date_maturity = line.date_maturity
                    if init_date_maturity:
                        vn_account_move_line_date_maturity = init_date_maturity
                    new_vn_account_move_line.append({
                        'move_id': line.move_id.id,
                        'account_id': line.account_id.id,
                        'name': line.name,
                        'ref': line.ref,
                        'quantity': line.quantity,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'debit': line.debit,
                        'credit': line.credit,
                        'balance': line.balance,
                        'amount_currency': line.amount_currency,
                        'price_subtotal': line.price_subtotal,
                        'reconciled': line.reconciled,
                        'blocked': line.blocked,
                        'date_maturity': vn_account_move_line_date_maturity,
                        'currency_id': line.currency_id.id,
                        'partner_id': line.partner_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'product_id': line.product_id.id,
                        'reconcile_model_id': line.reconcile_model_id.id,
                        'payment_id': line.payment_id.id,
                        'statement_line_id': line.statement_line_id.id,
                        'statement_id': line.statement_id.id,
                        'tax_ids': [(6, 0, line.tax_ids.ids)],
                        'tax_line_id': line.tax_line_id.id,
                        'tax_group_id': line.tax_group_id.id,
                        'tax_base_amount': line.tax_base_amount,
                        'tax_exigible': line.tax_exigible,
                        'tax_repartition_line_id': line.tax_repartition_line_id.id,
                        'tag_ids': [(6, 0, line.tag_ids.ids)],
                        'tax_audit': line.tax_audit,
                        'amount_residual': line.amount_residual,
                        'amount_residual_currency': line.amount_residual_currency,
                        'full_reconcile_id': line.full_reconcile_id.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                        'display_type': line.display_type,
                        'is_rounding_line': line.is_rounding_line,
                        'exclude_from_invoice_tab': line.exclude_from_invoice_tab,
                        'always_set_currency_id': line.always_set_currency_id.id,
                        'related_account_id': line.related_account_id.id,
                        'account_move_line_backup': line.id
                    })
                if rec.type == 'out_invoice' or rec.type == 'out_refund':
                    if rec.partner_id:
                        # get debit account id need to spilt
                        partner_debit_account_id = rec.partner_id.property_account_receivable_id.id
                        # start update vn_account_move_line
                        vn_account_move_line_need_create = []
                        line_backup = None
                        for line in new_vn_account_move_line:
                            if line['account_id'] == rec.partner_id.property_account_receivable_id.id:
                                line_backup = line
                        # random account_id if line_backup not found
                        if not line_backup:
                            # search if account_id == 1
                            line_backup_account_id = None
                            account_ids = [e['account_id'] for e in new_vn_account_move_line]
                            for e in account_ids:
                                if account_ids.count(e) == 1:
                                    line_backup_account_id = e
                            if line_backup_account_id:
                                for line in new_vn_account_move_line:
                                    if line['account_id'] == line_backup_account_id:
                                        line_backup = line
                        if line_backup:
                            for line in new_vn_account_move_line:
                                if line['account_id'] != rec.partner_id.property_account_receivable_id.id:
                                    line['related_account_id'] = partner_debit_account_id
                                    vn_account_move_line_need_create.append(line)
                                    new_line_backup = copy.deepcopy(line_backup)
                                    if line['debit'] > 0:
                                        new_line_backup['credit'] = line['debit']
                                        new_line_backup['debit'] = 0
                                        new_line_backup['amount_currency'] = -line['amount_currency']
                                        new_line_backup['related_account_id'] = line['account_id']
                                    else:
                                        new_line_backup['credit'] = 0
                                        new_line_backup['debit'] = line['credit']
                                        new_line_backup['amount_currency'] = -line['amount_currency']
                                        new_line_backup['related_account_id'] = line['account_id']
                                    vn_account_move_line_need_create.append(new_line_backup)
                        else:
                            print("linebackup==None")
                            print(rec)
                        result = self.env['vn.account.move.line'].create(vn_account_move_line_need_create)

                elif rec.type == 'in_invoice' or rec.type == 'in_refund':
                    if rec.partner_id:
                        # get debit account id need to spilt
                        partner_debit_account_id = rec.partner_id.property_account_payable_id.id
                        # start update vn_account_move_line
                        vn_account_move_line_need_create = []
                        line_backup = None
                        for line in new_vn_account_move_line:
                            if line['account_id'] == rec.partner_id.property_account_payable_id.id:
                                line_backup = line
                        # random account_id if line_backup not found
                        if not line_backup:
                            # search if account_id == 1
                            line_backup_account_id = None
                            account_ids = [e['account_id'] for e in new_vn_account_move_line]
                            for e in account_ids:
                                if account_ids.count(e) == 1:
                                    line_backup_account_id = e
                            if line_backup_account_id:
                                for line in new_vn_account_move_line:
                                    if line['account_id'] == line_backup_account_id:
                                        line_backup = line
                        if line_backup:
                            for line in new_vn_account_move_line:
                                if line['account_id'] != rec.partner_id.property_account_payable_id.id:
                                    line['related_account_id'] = partner_debit_account_id
                                    vn_account_move_line_need_create.append(line)
                                    new_line_backup = copy.deepcopy(line_backup)
                                    if line['debit'] > 0:
                                        new_line_backup['credit'] = line['debit']
                                        new_line_backup['debit'] = 0
                                        new_line_backup['amount_currency'] = -line['amount_currency']
                                        new_line_backup['related_account_id'] = line['account_id']
                                    else:
                                        new_line_backup['credit'] = 0
                                        new_line_backup['debit'] = line['credit']
                                        new_line_backup['amount_currency'] = -line['amount_currency']
                                        new_line_backup['related_account_id'] = line['account_id']
                                    vn_account_move_line_need_create.append(new_line_backup)
                            self.env['vn.account.move.line'].create(vn_account_move_line_need_create)
                        else:
                            print("linebackup==None")
                            print(rec)
                elif rec.type == 'entry':
                    # check if have to update
                    need_update_related_account_id = False
                    for line in new_vn_account_move_line:
                        if not line['related_account_id']:
                            need_update_related_account_id = True
                    if need_update_related_account_id:
                        # count debit line and credit line
                        vn_account_move_line_need_create = []
                        debit_account = None
                        debit_account_count = 0
                        credit_account = None
                        credit_account_count = 0
                        for line in new_vn_account_move_line:
                            if line['debit'] > 0:
                                debit_account = line['account_id']
                                debit_account_count += 1
                        for line in new_vn_account_move_line:
                            if line['credit'] > 0:
                                credit_account = line['account_id']
                                credit_account_count += 1
                        # if credit line == 1
                        if debit_account_count == 1:
                            line_backup = None
                            for line in new_vn_account_move_line:
                                if line['account_id'] == debit_account:
                                    line_backup = line
                            for line in new_vn_account_move_line:
                                if line['account_id'] != debit_account:
                                    line['related_account_id'] = debit_account
                                    vn_account_move_line_need_create.append(line)
                                    new_line_backup = copy.deepcopy(line_backup)
                                    if line['debit'] > 0:
                                        new_line_backup['credit'] = line['debit']
                                        new_line_backup['debit'] = 0
                                        new_line_backup['amount_currency'] = -line['amount_currency']
                                        new_line_backup['related_account_id'] = line['account_id']
                                    else:
                                        new_line_backup['credit'] = 0
                                        new_line_backup['debit'] = line['credit']
                                        new_line_backup['amount_currency'] = -line['amount_currency']
                                        new_line_backup['related_account_id'] = line['account_id']
                                    vn_account_move_line_need_create.append(new_line_backup)
                        # if debit line == 1
                        elif credit_account_count == 1:
                            line_backup = None
                            for line in new_vn_account_move_line:
                                if line['account_id'] == credit_account:
                                    line_backup = line
                            for line in new_vn_account_move_line:
                                if line['account_id'] != credit_account:
                                    line['related_account_id'] = credit_account
                                    vn_account_move_line_need_create.append(line)
                                    new_line_backup = copy.deepcopy(line_backup)
                                    if line['debit'] > 0:
                                        new_line_backup['credit'] = line['debit']
                                        new_line_backup['debit'] = 0
                                        new_line_backup['amount_currency'] = -line['amount_currency']
                                        new_line_backup['related_account_id'] = line['account_id']
                                    else:
                                        new_line_backup['credit'] = 0
                                        new_line_backup['debit'] = line['credit']
                                        new_line_backup['amount_currency'] = -line['amount_currency']
                                        new_line_backup['related_account_id'] = line['account_id']
                                    vn_account_move_line_need_create.append(new_line_backup)
                        self.env['vn.account.move.line'].create(vn_account_move_line_need_create)
                    else:
                        self.env['vn.account.move.line'].create(new_vn_account_move_line)
            except Exception as ex:
                traceback.print_exc(None, sys.stderr)
