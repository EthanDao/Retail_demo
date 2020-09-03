from odoo import fields, models, api
from odoo.tools import safe_eval


class VietNamAccountMoveLine(models.Model):
    _name = 'vn.account.move.line'
    _description = "Viet Nam Journal Item"
    _order = "date desc, move_name desc, id"
    _check_company_auto = True

    # ==== Business fields ====
    move_id = fields.Many2one('account.move', string='Journal Entry',
                              index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",
                              help="The move of this entry line.")
    move_name = fields.Char(string='Number', related='move_id.name', store=True, index=True)
    date = fields.Date(related='move_id.date', store=True, readonly=True, index=True, copy=False, group_operator='min')
    parent_state = fields.Selection(related='move_id.state', store=True, readonly=True)
    journal_id = fields.Many2one(related='move_id.journal_id', store=True, index=True, copy=False)
    company_id = fields.Many2one(related='move_id.company_id', store=True, readonly=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
                                          readonly=True, store=True,
                                          help='Utility field to express amount currency')
    country_id = fields.Many2one(comodel_name='res.country', related='move_id.company_id.country_id')
    account_id = fields.Many2one('account.account', string='Account',
                                 index=True, ondelete="cascade", check_company=True,
                                 domain=[('deprecated', '=', False)])
    account_id_dn_01_balance_positive = fields.Boolean(default=False)
    account_id_dn_01_balance_compare_positive = fields.Boolean(default=False)

    # phai thu ngan han
    account_id_dn_01_131_balance_positive = fields.Boolean(default=False)
    # phai thu dai han
    account_id_dn_01_211_balance_positive = fields.Boolean(default=False)
    # phai tra ngan han
    account_id_dn_01_311_balance_positive = fields.Boolean(default=False)
    # phai tra dai han
    account_id_dn_01_331_balance_positive = fields.Boolean(default=False)
    account_id_dn_01_131_balance_compare_positive = fields.Boolean(default=False)
    account_id_dn_01_211_balance_compare_positive = fields.Boolean(default=False)
    account_id_dn_01_311_balance_compare_positive = fields.Boolean(default=False)
    account_id_dn_01_331_balance_compare_positive = fields.Boolean(default=False)
    account_internal_type = fields.Selection(related='account_id.user_type_id.type', string="Internal Type", store=True,
                                             readonly=True)
    account_root_id = fields.Many2one(related='account_id.root_id', string="Account Root", store=True, readonly=True)
    name = fields.Char(string='Label')
    quantity = fields.Float(string='Quantity',
                            default=1.0, digits='Product Unit of Measure',
                            help="The optional quantity expressed by this line, eg: number of product sold. "
                                 "The quantity is not a legal requirement but is very useful for some reports.")
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    debit = fields.Monetary(string='Debit', default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(string='Credit', default=0.0, currency_field='company_currency_id')
    balance = fields.Monetary(string='Balance', store=True,
                              currency_field='company_currency_id',
                              compute='_compute_balance',
                              help="Technical field holding the debit - credit in order to open meaningful graph views from reports")
    amount_currency = fields.Monetary(string='Amount in Currency', store=True, copy=True,
                                      help="The amount expressed in an optional other currency if it is a multi-currency entry.")
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
                                     currency_field='always_set_currency_id')
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
                                  currency_field='always_set_currency_id')
    reconciled = fields.Boolean()
    blocked = fields.Boolean(string='No Follow-up', default=False,
                             help="You can check this box to mark this journal item as a litigation with the associated partner")
    date_maturity = fields.Date(string='Due Date', index=True,
                                help="This field is used for payable and receivable journal entries. You can put the limit date for the payment of this line.")
    date_maturity_short = fields.Boolean(string='Due Date Remain', index=True)
    date_maturity_compare_short = fields.Boolean(string='Due Date Compare Remain', index=True)
    date_maturity_3_short = fields.Boolean(string='Due Date Remain', index=True)
    date_maturity_3_compare_short = fields.Boolean(string='Due Date Compare Remain', index=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
    # phai thu ngan han
    partner_id_balance_b01_131_short_positive = fields.Boolean(default=False)
    # phai thu dai han
    partner_id_balance_b01_211_long_positive = fields.Boolean(default=False)
    # phai tra ngan han
    partner_id_balance_b01_311_short_positive = fields.Boolean(default=False)
    # phai tra dai han
    partner_id_balance_b01_331_long_positive = fields.Boolean(default=False)

    # phai thu ngan han
    partner_id_balance_b01_131_short_compare_positive = fields.Boolean(default=False)
    # phai thu dai han
    partner_id_balance_b01_211_long_compare_positive = fields.Boolean(default=False)
    # phai tra ngan han
    partner_id_balance_b01_311_short_compare_positive = fields.Boolean(default=False)
    # phai tra dai han
    partner_id_balance_b01_331_long_compare_positive = fields.Boolean(default=False)

    # phai thu ngan han
    non_partner_id_balance_b01_131_short_positive = fields.Boolean(default=False)
    # phai thu dai han
    non_partner_id_balance_b01_211_long_positive = fields.Boolean(default=False)
    # phai tra ngan han
    non_partner_id_balance_b01_311_short_positive = fields.Boolean(default=False)
    # phai tra dai han
    non_partner_id_balance_b01_331_long_positive = fields.Boolean(default=False)

    # phai thu ngan han
    non_partner_id_balance_b01_131_short_compare_positive = fields.Boolean(default=False)
    # phai thu dai han
    non_partner_id_balance_b01_211_long_compare_positive = fields.Boolean(default=False)
    # phai tra ngan han
    non_partner_id_balance_b01_311_short_compare_positive = fields.Boolean(default=False)
    # phai tra dai han
    non_partner_id_balance_b01_331_long_compare_positive = fields.Boolean(default=False)

    partner_id_balance_b01_132_short_positive = fields.Boolean(default=False)
    partner_id_balance_b01_132_long_positive = fields.Boolean(default=False)
    partner_id_balance_b01_136_positive = fields.Boolean(default=False)
    partner_id_balance_b01_139_positive = fields.Boolean(default=False)
    partner_id_balance_b01_215_positive = fields.Boolean(default=False)
    partner_id_balance_b01_153_positive = fields.Boolean(default=False)
    partner_id_balance_b01_216_positive = fields.Boolean(default=False)
    partner_id_balance_b01_313_positive = fields.Boolean(default=False)
    partner_id_balance_b01_314_positive = fields.Boolean(default=False)
    partner_id_balance_b01_318_positive = fields.Boolean(default=False)
    partner_id_balance_b01_319_positive = fields.Boolean(default=False)
    partner_id_balance_b01_336_positive = fields.Boolean(default=False)
    partner_id_balance_b01_337_positive = fields.Boolean(default=False)

    partner_id_balance_b01_132_short_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_132_long_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_136_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_139_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_215_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_153_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_216_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_313_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_314_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_318_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_319_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_336_compare_positive = fields.Boolean(default=False)
    partner_id_balance_b01_337_compare_positive = fields.Boolean(default=False)

    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    product_id = fields.Many2one('product.product', string='Product')

    # ==== Origin fields ====
    reconcile_model_id = fields.Many2one('account.reconcile.model', string="Reconciliation Model", copy=False,
                                         readonly=True)
    payment_id = fields.Many2one('account.payment', string="Originator Payment", copy=False,
                                 help="Payment that created this entry")
    is_long_payment = fields.Boolean(default=False)
    statement_line_id = fields.Many2one('account.bank.statement.line',
                                        string='Bank statement line reconciled with this entry',
                                        index=True, copy=False, readonly=True)
    statement_id = fields.Many2one(related='statement_line_id.statement_id', store=True, index=True, copy=False,
                                   help="The bank statement used for bank reconciliation")

    # ==== Tax fields ====
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount")
    tax_line_id = fields.Many2one('account.tax', string='Originator Tax', ondelete='restrict', store=True,
                                  help="Indicates that this journal item is a tax line")
    tax_group_id = fields.Many2one(related='tax_line_id.tax_group_id', string='Originator tax group',
                                   readonly=True, store=True,
                                   help='technical field for widget tax-group-custom-field')
    tax_base_amount = fields.Monetary(string="Base Amount", store=True, readonly=True,
                                      currency_field='company_currency_id')
    tax_exigible = fields.Boolean(string='Appears in VAT report', default=True, readonly=True,
                                  help="Technical field used to mark a tax line as exigible in the vat report or not (only exigible journal items"
                                       " are displayed). By default all new journal items are directly exigible, but with the feature cash_basis"
                                       " on taxes, some will become exigible only when the payment is recorded.")
    tax_repartition_line_id = fields.Many2one(comodel_name='account.tax.repartition.line',
                                              string="Originator Tax Repartition Line", ondelete='restrict',
                                              readonly=True,
                                              help="Tax repartition line that caused the creation of this move line, if any")
    tag_ids = fields.Many2many(string="Tags", comodel_name='account.account.tag', ondelete='restrict',
                               help="Tags assigned to this line by the tax creating it, if any. It determines its impact on financial reports.")
    tax_audit = fields.Char(string="Tax Audit String", store=True,
                            help="Computed field, listing the tax grids impacted by this line, and the amount it applies to each of them.")

    # ==== Reconciliation fields ====
    amount_residual = fields.Monetary(string='Residual Amount', store=True,
                                      currency_field='company_currency_id',
                                      help="The residual amount on a journal item expressed in the company currency.")
    amount_residual_currency = fields.Monetary(string='Residual Amount in Currency', store=True,
                                               help="The residual amount on a journal item expressed in its currency (possibly not the company currency).")
    full_reconcile_id = fields.Many2one('account.full.reconcile', string="Matching #", copy=False, index=True,
                                        readonly=True)
    ref = fields.Char(string='Reference')
    matched_debit_ids = fields.One2many('account.partial.reconcile', 'credit_move_id', string='Matched Debits',
                                        help='Debit journal items that are matched with this journal item.',
                                        readonly=True)
    matched_credit_ids = fields.One2many('account.partial.reconcile', 'debit_move_id', string='Matched Credits',
                                         help='Credit journal items that are matched with this journal item.',
                                         readonly=True)

    # ==== Analytic fields ====
    analytic_line_ids = fields.One2many('account.analytic.line', 'move_id', string='Analytic lines')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note'),
    ], default=False, help="Technical field for UX purpose.")
    is_rounding_line = fields.Boolean(help="Technical field used to retrieve the cash rounding line.")
    exclude_from_invoice_tab = fields.Boolean(
        help="Technical field used to exclude some lines from the invoice_line_ids tab in the form view.")
    always_set_currency_id = fields.Many2one('res.currency', string='Foreign Currency',
                                             help="Technical field used to compute the monetary field. As currency_id is not a required field, we need to use either the foreign currency, either the company one.")

    account_move_line_backup = fields.Many2one('account.move.line', string='Account Move Line Backup')

    def init(self):
        """ change index on partner_id to a multi-column index on (partner_id, ref), the new index will behave in the
            same way when we search on partner_id, with the addition of being optimal when having a query that will
            search on partner_id and ref at the same time (which is the case when we open the bank reconciliation widget)
        """
        cr = self._cr
        cr.execute('DROP INDEX IF EXISTS vn_account_move_line_partner_id_index')
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = %s',
                   ('vn_account_move_line_partner_id_ref_idx',))
        if not cr.fetchone():
            cr.execute('CREATE INDEX vn_account_move_line_partner_id_ref_idx ON vn_account_move_line (partner_id, ref)')

    related_account_id = fields.Many2one('account.account', string='Related Account')
    b01_dn = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_318 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_211 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_212 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_319 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_216 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_123 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_313 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_314 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_324 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_421 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_411 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_3381 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_241 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_141 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_337 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_136 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_335 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_255 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b01_dn_215 = fields.Integer(compute='_compute_b01_dn', store=True, index=True)
    b02_dn = fields.Integer(compute='_compute_b02_dn', store=True, index=True)
    b02_dn_51 = fields.Integer(compute='_compute_b02_dn', store=True, index=True)
    b02_dn_23 = fields.Integer(compute='_compute_b02_dn', store=True, index=True)
    account_contract_id = fields.Many2one('account.contract', string='Hợp đồng')
    b03_dn = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)
    b03_dn_111 = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)
    b03_dn_221 = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)
    b03_dn_36 = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)
    b03_dn_222 = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)
    b03_dn_7 = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)
    b03_dn_23 = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)
    b03_dn_25 = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)
    b03_dn_26 = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)
    b03_dn_27 = fields.Integer(
        compute='_compute_b03_dn', store=True, index=True)

    account_41112_type = fields.Selection(string='Loại tài khoản cổ phiếu',
                                          selection=[('fund', 'Vốn chủ sở hữu'), ('debit', 'Nợ phải trả')],
                                          default='fund', index=True)
    # wh_in_quantity = fields.Float(string='Số lượng nhập trong kỳ', group_operator='sum',
    #                               compute='_compute_wh_in_quantity', store=True, index=True)
    # wh_out_quantity = fields.Float(string='Số lượng xuất trong kỳ', group_operator='sum',
    #                                compute='_compute_wh_out_quantity',
    #                                store=True, index=True)
    # wh_in_total = fields.Float(string='Thành tiền', group_operator='sum', compute='_compute_wh_in_total', store=True, index=True)
    # wh_out_total = fields.Float(string='Thành tiền', group_operator='sum', compute='_compute_wh_out_total', store=True, index=True)
    location_id = fields.Many2one(
        'stock.location', 'Nhà kho')

    # wh_unit_price_avg = fields.Float(string='Đơn giá xuất BQGQ', group_operator='avg',
    #                                  compute='_compute_wh_unit_price_avg',
    #                                  store=True, index=True)

    # @api.depends('product_id', 'account_id', 'partner_id', 'balance', 'credit', 'debit', 'quantity')
    # def _compute_wh_in_quantity(self):
    #     for rec in self:
    #         if rec.balance > 0:
    #             rec.wh_in_quantity = rec.quantity
    #         else:
    #             rec.wh_in_quantity = 0
    #
    # @api.depends('product_id', 'account_id', 'partner_id', 'balance', 'credit', 'debit', 'quantity')
    # def _compute_wh_out_quantity(self):
    #     for rec in self:
    #         if rec.balance < 0:
    #             rec.wh_out_quantity = rec.quantity
    #         else:
    #             rec.wh_out_quantity = 0
    #
    # @api.depends('debit')
    # def _compute_wh_in_total(self):
    #     for rec in self:
    #         rec.wh_in_total = rec.credit
    #
    # @api.depends('credit')
    # def _compute_wh_out_total(self):
    #     for rec in self:
    #         rec.wh_out_total = rec.debit
    #
    # @api.depends('wh_out_total', 'wh_out_quantity')
    # def _compute_wh_unit_price_avg(self):
    #     for rec in self:
    #         if rec.wh_out_quantity == 0:
    #             rec.wh_unit_price_avg = 0
    #         else:
    #             rec.wh_unit_price_avg = rec.wh_out_total / rec.wh_out_quantity

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for line in self:
            line.balance = line.debit - line.credit

    @api.depends('product_id', 'account_id', 'partner_id', 'date_maturity', 'related_account_id')
    def _compute_b01_dn(self):
        # update for b01_dn
        for rec in self:
            rec.b01_dn = None
            if rec.account_id:
                updated = 0
                updated_318 = 0
                updated_319 = 0
                rec.b01_dn_241 = 0
                rec.b01_dn_141 = 0
                rec.b01_dn_337 = 0
                rec.b01_dn_335 = 0
                # 1. Tien
                if rec.account_id.code.startswith('111') or rec.account_id.code.startswith(
                        '112') or rec.account_id.code.startswith('113'):
                    rec.b01_dn = 111
                    updated += 1
                if (rec.account_id.code.startswith('1281') or rec.account_id.code.startswith(
                        '1288')):
                    rec.b01_dn = 112
                    updated += 1
                if rec.account_id.code.startswith('121'):
                    rec.b01_dn = 121
                    updated += 1
                if rec.account_id.code.startswith('2291'):
                    rec.b01_dn = 122
                    updated += 1
                if (rec.account_id.code.startswith('1281') or rec.account_id.code.startswith(
                        '1282') or rec.account_id.code.startswith('1288')):
                    rec.b01_dn_123 = 123
                if rec.account_id.code.startswith('131'):
                    rec.b01_dn = 131
                    updated += 1
                if rec.account_id.code.startswith('331'):
                    rec.b01_dn = 132
                    updated += 1
                if (rec.account_id.code.startswith('1362') or rec.account_id.code.startswith(
                        '1363') or rec.account_id.code.startswith('1368')):
                    rec.b01_dn = 133
                    updated += 1
                if rec.account_id.code.startswith('337'):
                    rec.b01_dn = 134
                    updated += 1
                if rec.account_id.code.startswith('1283'):
                    rec.b01_dn = 135
                    updated += 1
                if (rec.account_id.code.startswith('1385') or rec.account_id.code.startswith(
                        '1388') or rec.account_id.code.startswith(
                    '334') or rec.account_id.code.startswith('338') or rec.account_id.code.startswith(
                    '141') or rec.account_id.code.startswith('244')):
                    rec.b01_dn_136 = 136
                    # updated += 1
                if rec.account_id.code.startswith('2293'):
                    rec.b01_dn = 137
                    updated += 1
                if rec.account_id.code.startswith('1381'):
                    rec.b01_dn = 139
                    updated += 1
                if rec.account_id.code.startswith('151') or rec.account_id.code.startswith(
                        '152') or rec.account_id.code.startswith(
                    '153') or rec.account_id.code.startswith('154') or rec.account_id.code.startswith(
                    '155') or rec.account_id.code.startswith(
                    '156') or rec.account_id.code.startswith('157') or rec.account_id.code.startswith(
                    '158'):
                    rec.b01_dn_141 = 141
                    updated += 1
                if rec.account_id.code.startswith('2294'):
                    rec.b01_dn = 149
                    updated += 1
                if rec.account_id.code.startswith('242'):
                    rec.b01_dn = 151
                    updated += 1
                if rec.account_id.code.startswith('133'):
                    rec.b01_dn = 152
                    updated += 1
                if rec.account_id.code.startswith('333'):
                    rec.b01_dn = 153
                    updated += 1
                if rec.account_id.code.startswith('171'):
                    rec.b01_dn = 154
                    updated += 1
                if rec.account_id.code.startswith('2288'):
                    rec.b01_dn = 155
                    updated += 1
                # if rec.account_id.code.startswith('131'):
                #     rec.b01_dn_211 = 211
                # updated += 1
                # if rec.account_id.code.startswith('331'):
                #     rec.b01_dn_212 = 212
                # updated += 1
                if rec.account_id.code.startswith('1361'):
                    rec.b01_dn = 213
                    updated += 1
                if (rec.account_id.code.startswith('1362') or rec.account_id.code.startswith(
                        '1363') or rec.account_id.code.startswith('1368')):
                    rec.b01_dn = 214
                    updated += 1
                if rec.account_id.code.startswith('1283'):
                    rec.b01_dn_215 = 215
                    # updated += 1
                if ((rec.account_id.code.startswith('1385') or rec.account_id.code.startswith(
                        '1388') or rec.account_id.code.startswith('334') or rec.account_id.code.startswith(
                    '338') or rec.account_id.code.startswith('141'))) or rec.account_id.code.startswith(
                    '244'):
                    rec.b01_dn_216 = 216
                if rec.account_id.code.startswith('2293'):
                    rec.b01_dn = 219
                    updated += 1
                if rec.account_id.code.startswith('211'):
                    rec.b01_dn = 222
                    updated += 1
                if rec.account_id.code.startswith('2141'):
                    rec.b01_dn = 223
                    updated += 1
                if rec.account_id.code.startswith('212'):
                    rec.b01_dn = 225
                    updated += 1
                if rec.account_id.code.startswith('2142'):
                    rec.b01_dn = 226
                    updated += 1
                if rec.account_id.code.startswith('213'):
                    rec.b01_dn = 228
                    updated += 1
                if rec.account_id.code.startswith('2143'):
                    rec.b01_dn = 229
                    updated += 1
                if rec.account_id.code.startswith('217'):
                    rec.b01_dn = 231
                    updated += 1
                if rec.account_id.code.startswith('2147'):
                    rec.b01_dn = 232
                    updated += 1
                if (rec.account_id.code.startswith('154') or rec.account_id.code.startswith(
                        '2249')):
                    rec.b01_dn_241 = 241
                    # updated += 1
                if rec.account_id.code.startswith('241'):
                    rec.b01_dn = 242
                    updated += 1
                if rec.account_id.code.startswith('221'):
                    rec.b01_dn = 251
                    updated += 1
                if rec.account_id.code.startswith('222'):
                    rec.b01_dn = 252
                    updated += 1
                if rec.account_id.code.startswith('2281'):
                    rec.b01_dn = 253
                    updated += 1
                if rec.account_id.code.startswith('2292'):
                    rec.b01_dn = 254
                    updated += 1
                if (rec.account_id.code.startswith('1281') or rec.account_id.code.startswith(
                        '1282') or rec.account_id.code.startswith('1288')):
                    rec.b01_dn_255 = 255
                    # updated += 1
                # if rec.account_id.code.startswith('2422'):
                #     rec.b01_dn = 261
                #     updated += 1
                if rec.account_id.code.startswith('243'):
                    rec.b01_dn = 262
                    updated += 1
                if (rec.account_id.code.startswith('1534') or rec.account_id.code.startswith(
                        '2294')):
                    rec.b01_dn = 263
                    updated += 1
                # if rec.account_id.code.startswith('2288'):
                #     rec.b01_dn = 268
                #     updated += 1
                # if rec.account_id.code.startswith(
                #         '331') and rec.due_date_default < 12:
                #     rec.b01_dn = 311
                # updated += 1
                # Trong truong hop nay do tuong tu 131 nen lay tu dong 132

                # if (rec.related_account_id.code.startswith('131') or rec.account_id.code.startswith(
                #         '131')) and rec.due_date_default < 12:
                #     rec.b01_dn = 312
                #     updated += 1
                # Trong truong hop nay do tuong tu 131 nen lay tu dong 131
                if rec.account_id.code.startswith(
                        '333'):
                    rec.b01_dn_313 = 313
                    # updated += 1
                if rec.account_id.code.startswith(
                        '334'):
                    rec.b01_dn_314 = 314
                    # updated += 1
                if rec.account_id.code.startswith(
                        '335'):
                    rec.b01_dn = 315
                    updated += 1
                if (rec.account_id.code.startswith(
                        '3362') or rec.account_id.code.startswith(
                    '3363') or rec.account_id.code.startswith('3368')):
                    rec.b01_dn = 316
                    updated += 1
                if rec.account_id.code.startswith('337'):
                    rec.b01_dn = 317
                    updated += 1
                if rec.account_id.code.startswith(
                        '3387'):
                    rec.b01_dn_318 = 318
                    updated_318 += 1
                if (rec.account_id.code.startswith(
                        '338') or rec.account_id.code.startswith(
                    '138') or rec.account_id.code.startswith('344')):
                    rec.b01_dn_319 = 319
                    updated_319 += 1
                if rec.account_id.code.startswith('341') or rec.account_id.code.startswith('34311'):
                    rec.b01_dn = 320
                    updated += 1
                if rec.account_id.code.startswith(
                        '352'):
                    rec.b01_dn = 321
                    updated += 1
                if rec.account_id.code.startswith('353'):
                    rec.b01_dn = 322
                    updated += 1
                if rec.account_id.code.startswith('357'):
                    rec.b01_dn = 323
                    updated += 1
                if rec.account_id.code.startswith('171'):
                    rec.b01_dn_324 = 324
                    # updated += 1
                # if rec.account_id.code.startswith(
                #         '331'):
                #     rec.b01_dn = 331
                #     updated += 1
                # if rec.account_id.code.startswith(
                #         '131'):
                #     rec.b01_dn = 332
                #     updated += 1
                # if rec.account_id.code.startswith(
                #         '335'):
                #     rec.b01_dn = 333
                #     updated += 1
                if rec.account_id.code.startswith('3361'):
                    rec.b01_dn = 334
                    updated += 1
                if (rec.account_id.code.startswith(
                        '3362') or rec.account_id.code.startswith(
                    '3363') or rec.account_id.code.startswith('3368')):
                    rec.b01_dn_335 = 335
                    # updated += 1
                if rec.account_id.code.startswith(
                        '3387'):
                    rec.b01_dn = 336
                    updated += 1
                if (rec.account_id.code.startswith('338') or rec.account_id.code.startswith(
                        '344')):
                    rec.b01_dn_337 = 337
                    # updated += 1
                if rec.account_id.code.startswith('341'):
                    rec.b01_dn_3381 = 3381
                    # updated += 1
                if rec.account_id.code.startswith('34311'):
                    rec.b01_dn = 3382
                    updated += 1
                if rec.account_id.code.startswith('34312'):
                    rec.b01_dn = 3383
                    updated += 1
                if rec.account_id.code.startswith('34313'):
                    rec.b01_dn = 3384
                    updated += 1
                if rec.account_id.code.startswith('3432'):
                    rec.b01_dn = 339
                    updated += 1
                if rec.account_id.code.startswith(
                        '41112') and rec.account_41112_type == 'debit':
                    rec.b01_dn = 340
                    updated += 1
                if rec.account_id.code.startswith('347'):
                    rec.b01_dn = 341
                    updated += 1
                if rec.account_id.code.startswith(
                        '352'):
                    rec.b01_dn = 342
                    updated += 1
                if rec.account_id.code.startswith('356'):
                    rec.b01_dn = 343
                    updated += 1
                if rec.account_id.code.startswith('4111'):
                    rec.b01_dn_411 = 411
                    # updated += 1
                if rec.account_id.code.startswith('41111'):
                    rec.b01_dn = 4111
                    updated += 1
                if rec.account_id.code.startswith(
                        '41112') and rec.account_41112_type == 'fund':
                    rec.b01_dn = 4112
                    updated += 1
                if rec.account_id.code.startswith('4112'):
                    rec.b01_dn = 412
                    updated += 1
                if rec.account_id.code.startswith('4113'):
                    rec.b01_dn = 413
                    updated += 1
                if rec.account_id.code.startswith('4118'):
                    rec.b01_dn = 414
                    updated += 1
                if rec.account_id.code.startswith('419'):
                    rec.b01_dn = 415
                    updated += 1
                if rec.account_id.code.startswith('412'):
                    rec.b01_dn = 416
                    updated += 1
                if rec.account_id.code.startswith('413'):
                    rec.b01_dn = 417
                    updated += 1
                if rec.account_id.code.startswith('414'):
                    rec.b01_dn = 418
                    updated += 1
                if rec.account_id.code.startswith('417'):
                    rec.b01_dn = 419
                    updated += 1
                if rec.account_id.code.startswith('418'):
                    rec.b01_dn = 420
                    updated += 1
                if rec.account_id.code.startswith('421'):
                    rec.b01_dn_421 = 421
                    # updated += 1
                if rec.account_id.code.startswith('4211'):
                    rec.b01_dn = 4211
                    updated += 1
                if rec.account_id.code.startswith('4212'):
                    rec.b01_dn = 4212
                    updated += 1
                if rec.account_id.code.startswith('441'):
                    rec.b01_dn = 422
                    updated += 1
                if rec.account_id.code.startswith('461'):
                    rec.b01_dn = 4311
                    updated += 1
                if rec.account_id.code.startswith('161'):
                    rec.b01_dn = 4312
                    updated += 1
                if rec.account_id.code.startswith('466'):
                    rec.b01_dn = 432
                    updated += 1
                if updated > 1:
                    print('_compute_b01_dn: updated > 1: ' + str(rec.b01_dn))

    @api.depends('product_id', 'account_id', 'partner_id', 'date_maturity', 'related_account_id')
    def _compute_b02_dn(self):
        # update for b01_dn
        for rec in self:
            rec.b02_dn = None
            if rec.account_id and rec.related_account_id:
                updated = 0
                # 1. Tien
                if rec.account_id.code.startswith('511') and rec.credit > 0:
                    rec.b02_dn = 1
                    updated += 1
                # if ((rec.account_id.code.startswith('511') and rec.related_account_id.code.startswith('521')) or (
                #         rec.account_id.code.startswith('511') and rec.related_account_id.code.startswith(
                #     '333'))) and rec.debit > 0:
                #     rec.b02_dn = 2
                #     updated += 1
                if ((rec.account_id.code.startswith('511') and rec.related_account_id.code.startswith('521')) or (
                        rec.account_id.code.startswith('511') and rec.related_account_id.code.startswith('3333'))) and rec.debit > 0:
                    rec.b02_dn = 2
                    updated += 1
                if rec.account_id.code.startswith(
                        '911') and rec.related_account_id.code.startswith('632') and rec.debit > 0:
                    rec.b02_dn = 11
                    updated += 1
                if rec.account_id.code.startswith('515') and rec.related_account_id.code.startswith(
                        '911') and rec.debit > 0:
                    rec.b02_dn = 21
                    updated += 1
                if rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith(
                        '635') and rec.debit > 0:
                    rec.b02_dn = 22
                    updated += 1
                if rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith('6351') and rec.debit > 0:
                    rec.b02_dn_23 = 23
                    # updated += 1
                if rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith('641') and rec.debit > 0:
                    rec.b02_dn = 25
                    updated += 1
                if rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith('642') and rec.debit > 0:
                    rec.b02_dn = 26
                    updated += 1
                if rec.account_id.code.startswith('711') and rec.related_account_id.code.startswith(
                        '911') and rec.debit > 0:
                    rec.b02_dn = 31
                    updated += 1
                if rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith(
                        '811') and rec.debit > 0:
                    rec.b02_dn = 32
                    updated += 1
                # if (rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith('8211')) or (
                #         rec.account_id.code.startswith('8211') and rec.related_account_id.code.startswith('911')):
                #     rec.b02_dn = 51
                #     updated += 1
                if rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith(
                        '821') and rec.debit > 0:
                    rec.b02_dn_51 = 51
                    # updated += 1
                # if rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith(
                #         '8211') and rec.debit > 0:
                #     rec.b02_dn = 511
                #     updated += 1
                # if rec.account_id.code.startswith('8211') and rec.related_account_id.code.startswith(
                #         '911') and rec.credit > 0:
                #     rec.b02_dn = 512
                #     updated += 1
                # if (rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith('8212')) or (
                #         rec.account_id.code.startswith('8212') and rec.related_account_id.code.startswith('911')):
                #     rec.b02_dn = 52
                #     updated += 1
                if rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith(
                        '8212') and rec.debit > 0:
                    rec.b02_dn = 52
                    updated += 1
                # if rec.account_id.code.startswith('911') and rec.related_account_id.code.startswith(
                #         '8212') and rec.debit > 0:
                #     rec.b02_dn = 521
                #     updated += 1
                # if rec.account_id.code.startswith('8212') and rec.related_account_id.code.startswith(
                #         '911') and rec.credit > 0:
                #     rec.b02_dn = 522
                #     updated += 1
                if updated > 1:
                    print('_compute_b02_dn: updated > 1: ' + str(rec.b02_dn))

    @api.depends('product_id', 'account_id', 'partner_id', 'date_maturity', 'related_account_id')
    def _compute_b03_dn(self):
        # update for b01_dn
        for rec in self:
            rec.b03_dn = None
            if rec.account_id and rec.related_account_id:
                updated = 0
                # 1. Tien
                if (rec.account_id.code.startswith('111') or rec.account_id.code.startswith('112')) and (
                        rec.related_account_id.code.startswith('511') or rec.related_account_id.code.startswith(
                    '3331') or rec.related_account_id.code.startswith(
                    '131') or rec.related_account_id.code.startswith(
                    '515') or rec.related_account_id.code.startswith('121')) and rec.debit > 0:
                    rec.b03_dn = 1
                    updated += 1

                if (rec.account_id.code.startswith('331') or rec.account_id.code.startswith(
                        '151') or rec.account_id.code.startswith(
                    '152') or rec.account_id.code.startswith('153') or rec.account_id.code.startswith(
                    '154') or rec.account_id.code.startswith(
                    '155') or rec.account_id.code.startswith(
                    '156') or rec.account_id.code.startswith(
                    '157') or rec.account_id.code.startswith(
                    '158')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112')) and rec.debit > 0:
                    rec.b03_dn = 2
                    updated += 1
                if rec.account_id.code.startswith('334') and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112')) and rec.debit > 0:
                    rec.b03_dn = 3
                    updated += 1
                if (rec.account_id.code.startswith('635') or rec.account_id.code.startswith(
                        '335') or rec.account_id.code.startswith('242')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith('113')) and rec.debit > 0:
                    rec.b03_dn = 4
                    updated += 1
                if rec.account_id.code.startswith('3334') and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith('113')) and rec.debit > 0:
                    rec.b03_dn = 5
                    updated += 1
                if (rec.account_id.code.startswith('111') or rec.account_id.code.startswith('112')) and (
                        rec.related_account_id.code.startswith('711') or rec.related_account_id.code.startswith(
                    '133') or rec.related_account_id.code.startswith(
                    '141') or rec.related_account_id.code.startswith('244')) and rec.debit > 0:
                    rec.b03_dn = 6
                    updated += 1
                if (rec.account_id.code.startswith('811') or rec.account_id.code.startswith(
                        '161') or rec.account_id.code.startswith('244') or rec.account_id.code.startswith(
                    '333') or rec.account_id.code.startswith('338') or rec.account_id.code.startswith(
                    '344') or rec.account_id.code.startswith('352') or rec.account_id.code.startswith(
                    '353') or rec.account_id.code.startswith('356')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith('113')) and rec.debit > 0:
                    rec.b03_dn_7 = 7
                    # updated += 1
                if (rec.account_id.code.startswith('211') or rec.account_id.code.startswith(
                        '213') or rec.account_id.code.startswith('217') or rec.account_id.code.startswith('241')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith('113')) and rec.debit > 0:
                    rec.b03_dn = 21
                    updated += 1
                if (rec.account_id.code.startswith('111') or rec.account_id.code.startswith(
                        '112') or rec.account_id.code.startswith('113')) and (
                        rec.related_account_id.code.startswith('711') or rec.related_account_id.code.startswith(
                    '5117') or rec.related_account_id.code.startswith(
                    '131')) and rec.debit > 0 and rec.move_id.is_liquidation_invoice:
                    rec.b03_dn_221 = 221
                    # updated += 1
                if (rec.account_id.code.startswith('632') or rec.account_id.code.startswith('811')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith(
                    '113')) and rec.debit > 0 and rec.move_id.is_liquidation_invoice:
                    rec.b03_dn_222 = 222
                    # updated += 1
                if (rec.account_id.code.startswith('128') or rec.account_id.code.startswith(
                        '171')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith(
                    '113')) and rec.debit > 0:
                    rec.b03_dn_23 = 23
                    # updated += 1
                if (
                        rec.account_id.code.startswith('111') or rec.account_id.code.startswith(
                    '112') or rec.account_id.code.startswith(
                    '113')) and (
                        rec.related_account_id.code.startswith('128') or rec.related_account_id.code.startswith(
                    '171')) and rec.debit > 0:
                    rec.b03_dn = 24
                    updated += 1
                if (rec.account_id.code.startswith('221') or rec.account_id.code.startswith(
                        '222') or rec.account_id.code.startswith(
                    '2281')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith(
                    '113')) and rec.debit > 0:
                    rec.b03_dn_25 = 25
                    # updated += 1
                if (rec.account_id.code.startswith('111') or rec.account_id.code.startswith(
                        '112') or rec.account_id.code.startswith(
                    '113')) and (
                        rec.related_account_id.code.startswith('221') or rec.related_account_id.code.startswith(
                    '222') or rec.related_account_id.code.startswith(
                    '2281') or rec.related_account_id.code.startswith(
                    '131')) and rec.debit > 0:
                    rec.b03_dn_26 = 26
                    # updated += 1
                if (rec.account_id.code.startswith('111') or rec.account_id.code.startswith(
                        '112')) and rec.related_account_id.code.startswith('515') and rec.debit > 0:
                    rec.b03_dn_27 = 27
                    # updated += 1
                if (rec.account_id.code.startswith('111') or rec.account_id.code.startswith(
                        '112') or rec.account_id.code.startswith(
                    '113')) and rec.related_account_id.code.startswith('411') and rec.debit > 0:
                    rec.b03_dn = 31
                    updated += 1
                if (rec.account_id.code.startswith('411') or rec.account_id.code.startswith('419')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith(
                    '113')) and rec.debit > 0:
                    rec.b03_dn = 32
                    updated += 1
                if (rec.account_id.code.startswith('111') or rec.account_id.code.startswith(
                        '112') or rec.account_id.code.startswith(
                    '113')) and (
                        rec.related_account_id.code.startswith('3411') or rec.related_account_id.code.startswith(
                    '3431') or rec.related_account_id.code.startswith('3432') or rec.related_account_id.code.startswith(
                    '41112')) and rec.debit > 0:
                    rec.b03_dn = 33
                    updated += 1
                if (rec.account_id.code.startswith('3411') or rec.account_id.code.startswith(
                        '3431') or rec.account_id.code.startswith('3432') or rec.account_id.code.startswith(
                    '41112')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith(
                    '113')) and rec.debit > 0:
                    rec.b03_dn = 34
                    updated += 1
                if rec.account_id.code.startswith('3412') and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith(
                    '113')) and rec.debit > 0:
                    rec.b03_dn = 35
                    updated += 1
                if (rec.account_id.code.startswith('421') or rec.account_id.code.startswith('338')) and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith(
                    '113')) and rec.debit > 0:
                    rec.b03_dn_36 = 36
                    # updated += 1
                if rec.account_id.code.startswith('111') or rec.account_id.code.startswith(
                        '112') or rec.account_id.code.startswith('113'):
                    rec.b03_dn_111 = 111
                    # updated += 1
                # if (rec.account_id.code.startswith('1281') or rec.account_id.code.startswith(
                #         '1288')) and rec.due_date_default <= 3:
                if (rec.account_id.code.startswith('1281') or rec.account_id.code.startswith(
                        '1288')):
                    rec.b03_dn = 112
                    updated += 1
                if (rec.account_id.code.startswith('111') or rec.account_id.code.startswith(
                        '112') or rec.account_id.code.startswith(
                    '113')) and rec.related_account_id.code.startswith('4131') and rec.debit > 0:
                    rec.b03_dn = 611
                    updated += 1
                if rec.account_id.code.startswith('4131') and (
                        rec.related_account_id.code.startswith('111') or rec.related_account_id.code.startswith(
                    '112') or rec.related_account_id.code.startswith(
                    '113')) and rec.debit > 0:
                    rec.b03_dn = 612
                    updated += 1
                if updated > 1:
                    print('_compute_b03_dn: updated > 1: ' + str(rec.b03_dn))

    def _onchange_amount_currency(self):
        for line in self:
            if not line.currency_id:
                continue
            if not line.move_id.is_invoice(include_receipts=True):
                line._recompute_debit_credit_from_amount_currency()
                continue
            line.update(line._get_fields_onchange_balance(
                balance=line.amount_currency,
            ))
            line.update(line._get_price_total_and_subtotal())

    def _onchange_balance(self):
        for line in self:
            if line.currency_id:
                continue
            if not line.move_id.is_invoice(include_receipts=True):
                continue
            line.update(line._get_fields_onchange_balance())
            line.update(line._get_price_total_and_subtotal())

    def _get_fields_onchange_balance(self, quantity=None, discount=None, balance=None, move_type=None, currency=None,
                                     taxes=None, price_subtotal=None):
        self.ensure_one()
        return self._get_fields_onchange_balance_model(
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            balance=balance or self.balance,
            move_type=move_type or self.move_id.type,
            currency=currency or self.currency_id or self.move_id.currency_id,
            taxes=taxes or self.tax_ids,
            price_subtotal=price_subtotal or self.price_subtotal,
        )

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, balance, move_type, currency, taxes,
                                           price_subtotal):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param balance:         The new balance.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        balance *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if currency.is_zero(balance - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10
            taxes_res = taxes._origin.compute_all(balance, currency=currency, handle_price_include=False)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    balance += tax_res['amount']

        discount_factor = 1 - (discount / 100.0)
        if balance and discount_factor:
            # discount != 100%
            vals = {
                'quantity': quantity or 1.0,
                'price_unit': balance / discount_factor / (quantity or 1.0),
            }
        elif balance and not discount_factor:
            # discount == 100%
            vals = {
                'quantity': quantity or 1.0,
                'discount': 0.0,
                'price_unit': balance / (quantity or 1.0),
            }
        elif not discount_factor:
            # balance of line is 0, but discount  == 100% so we display the normal unit_price
            vals = {}
        else:
            # balance is 0, so unit price is 0 as well
            vals = {'price_unit': 0.0}
        return vals

    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None,
                                      partner=None, taxes=None, move_type=None):
        self.ensure_one()
        return self._get_price_total_and_subtotal_model(
            price_unit=price_unit or self.price_unit,
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            currency=currency or self.currency_id,
            product=product or self.product_id,
            partner=partner or self.partner_id,
            taxes=taxes or self.tax_ids,
            move_type=move_type or self.move_id.type,
        )

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * price_unit_wo_discount

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.compute_all(price_unit_wo_discount,
                                                  quantity=quantity, currency=currency, product=product,
                                                  partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    @api.model
    def _query_get(self, domain=None):
        self.check_access_rights('read')

        context = dict(self._context or {})
        domain = domain or []
        if not isinstance(domain, (list, tuple)):
            domain = safe_eval(domain)

        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]
        if context.get('date_from'):
            if not context.get('strict_range'):
                domain += ['|', (date_field, '>=', context['date_from']),
                           ('account_id.user_type_id.include_initial_balance', '=', True)]
            elif context.get('initial_bal'):
                domain += [(date_field, '<', context['date_from'])]
            else:
                domain += [(date_field, '>=', context['date_from'])]

        if context.get('journal_ids'):
            domain += [('journal_id', 'in', context['journal_ids'])]

        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('move_id.state', '=', state)]

        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]

        if 'company_ids' in context:
            domain += [('company_id', 'in', context['company_ids'])]

        if context.get('reconcile_date'):
            domain += ['|', ('reconciled', '=', False), '|',
                       ('matched_debit_ids.max_date', '>', context['reconcile_date']),
                       ('matched_credit_ids.max_date', '>', context['reconcile_date'])]

        if context.get('account_tag_ids'):
            domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]

        if context.get('account_ids'):
            domain += [('account_id', 'in', context['account_ids'].ids)]

        if context.get('analytic_tag_ids'):
            domain += [('analytic_tag_ids', 'in', context['analytic_tag_ids'].ids)]

        if context.get('analytic_account_ids'):
            domain += [('analytic_account_id', 'in', context['analytic_account_ids'].ids)]

        if context.get('partner_ids'):
            domain += [('partner_id', 'in', context['partner_ids'].ids)]

        if context.get('partner_categories'):
            domain += [('partner_id.category_id', 'in', context['partner_categories'].ids)]

        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
            domain.append(('display_type', 'not in', ('line_section', 'line_note')))
            domain.append(('move_id.state', '!=', 'cancel'))

            query = self._where_calc(domain)

            # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
            self._apply_ir_rules(query)

            tables, where_clause, where_clause_params = query.get_sql()
        return tables, where_clause, where_clause_params
