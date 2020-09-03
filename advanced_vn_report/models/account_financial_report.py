import ast
import copy
from datetime import datetime, timedelta

from odoo import models, fields, _
from odoo.tools import float_is_zero, ustr
from odoo.tools.safe_eval import safe_eval
import logging
# from profilehooks import profile

_logger = logging.getLogger(__name__)

countx = 0


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"
    is_compute_dn_01_account_balance_positive = fields.Boolean()
    is_compute_dn_01_account_balance_compare_positive = fields.Boolean()
    is_compute_dn_01_partner_balance_positive = fields.Boolean()
    is_compute_vn_date_due_remain = fields.Boolean()
    is_compute_vn_date_due_compare_remain = fields.Boolean()

    def get_report_informations(self, options):
        result = super(ReportAccountFinancialReport, self).get_report_informations(options)
        self.env['account.financial.html.report'].env.all.towrite = {}
        self.env['account.financial.html.report.line'].env.all.towrite = {}
        return result

    def is_our_vn_report(self):
        is_our_vn_report = False
        external_data = self.env['ir.model.data'].search([('model', '=', 'account.financial.html.report'), ('res_id', '=', self.id)])
        if external_data:
            if external_data.name == 'account_financial_report_b01':
                is_our_vn_report = 1
            elif external_data.name == 'account_financial_report_pnl_b02':
                is_our_vn_report = 2
            elif external_data.name == 'account_financial_report_cash_flow_statement_b03':
                is_our_vn_report = 3
        return is_our_vn_report

    def _get_lines(self, options, line_id=None):
        for rec in self:
            if rec.is_our_vn_report:
                rec.is_compute_dn_01_account_balance_positive = False
                rec.is_compute_dn_01_partner_balance_positive = False
                rec.is_compute_dn_01_account_balance_compare_positive = False
                rec.is_compute_vn_date_due_remain = False
                rec.is_compute_vn_date_due_compare_remain = False
                rec.is_compute_vn_date_due_3_remain = False
                rec.is_compute_vn_date_due_3_compare_remain = False
                if 'comparison' in options:
                    if 'number_period' in options['comparison']:
                        if options['comparison']['number_period'] > 1:
                            options['comparison']['number_period'] = 1
        return super(ReportAccountFinancialReport, self)._get_lines(options, line_id)


class AccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report.line"

    report_code = fields.Char("Mã")
    hide_if_negative = fields.Boolean(default=False)
    hide_if_positive = fields.Boolean(default=False)
    need_recompute = fields.Boolean(default=False)

    def is_our_vn_report(self):
        is_our_vn_report = False
        external_data = self.env['ir.model.data'].search([('model', '=', 'account.financial.html.report'), ('res_id', '=', self.financial_report_id.id)])
        if external_data:
            if external_data.name == 'account_financial_report_b01':
                is_our_vn_report = 1
            elif external_data.name == 'account_financial_report_pnl_b02':
                is_our_vn_report = 2
            elif external_data.name == 'account_financial_report_cash_flow_statement_b03':
                is_our_vn_report = 3
        return is_our_vn_report

    def _compute_line(self, currency_table, financial_report, group_by=None, domain=[]):
        """ Computes the sum that appeas on report lines when they aren't unfolded. It is using _query_get() function
            of account.move.line which is based on the context, and an additional domain (the field domain on the report
            line) to build the query that will be used.

            @param currency_table: dictionary containing the foreign currencies (key) and their factor (value)
                compared to the current user's company currency
            @param financial_report: browse_record of the financial report we are willing to compute the lines for
            @param group_by: used in case of conditionnal sums on the report line
            @param domain: domain on the report line to consider in the query_get() call

            @returns : a dictionnary that has for each aml in the domain a dictionnary of the values of the fields
        """
        domain = domain and ast.literal_eval(ustr(domain))
        for index, condition in enumerate(domain):
            if condition[0].startswith('tax_ids.'):
                new_condition = (condition[0].partition('.')[2], condition[1], condition[2])
                taxes = self.env['account.tax'].with_context(active_test=False).search([new_condition])
                domain[index] = ('tax_ids', 'in', taxes.ids)
        # start logan

        # check if our report get from vn.account.move.line
        aml_obj = self.env['account.move.line']
        is_our_vn_report = self.is_our_vn_report()
        if is_our_vn_report:
            aml_obj = self.env['vn.account.move.line']

        # end logan
        tables, where_clause, where_params = aml_obj._query_get(domain=self._get_aml_domain())
        # start logan
        if is_our_vn_report:
            if financial_report.tax_report:
                where_clause += ''' AND "account_move_line".tax_exigible = 't' '''
        else:
            if financial_report.tax_report:
                where_clause += ''' AND "vn_account_move_line".tax_exigible = 't' '''
        # end logan

        line = self
        financial_report = self._get_financial_report()

        select, select_params = self._query_get_select_sum(currency_table)
        where_params = select_params + where_params

        if (self.env.context.get('sum_if_pos') or self.env.context.get('sum_if_neg')) and group_by:
            if is_our_vn_report:
                sql = "SELECT vn_account_move_line." + group_by + " as " + group_by + "," + select + " FROM " + tables + " WHERE " + where_clause + " GROUP BY account_move_line." + group_by
                self.env.cr.execute(sql, where_params)
            else:
                sql = "SELECT account_move_line." + group_by + " as " + group_by + "," + select + " FROM " + tables + " WHERE " + where_clause + " GROUP BY account_move_line." + group_by
                self.env.cr.execute(sql, where_params)
            res = {'balance': 0, 'debit': 0, 'credit': 0, 'amount_residual': 0}
            for row in self.env.cr.dictfetchall():
                if (row['balance'] > 0 and self.env.context.get('sum_if_pos')) or (row['balance'] < 0 and self.env.context.get('sum_if_neg')):
                    for field in ['debit', 'credit', 'balance', 'amount_residual']:
                        res[field] += row[field]
            res['currency_id'] = self.env.company.currency_id.id
            return res

        sql, params = self._build_query_compute_line(select, tables, where_clause, where_params)
        self.env.cr.execute(sql, params)
        results = self.env.cr.dictfetchall()[0]
        results['currency_id'] = self.env.company.currency_id.id
        return results

    def _query_get_select_sum(self, currency_table):
        """ Little function to help building the SELECT statement when computing the report lines.

            @param currency_table: dictionary containing the foreign currencies (key) and their factor (value)
                compared to the current user's company currency
            @returns: the string and parameters to use for the SELECT
        """
        decimal_places = self.env.company.currency_id.decimal_places
        extra_params = []

        # start logan
        is_our_vn_report = self.is_our_vn_report()
        if is_our_vn_report:
            select = '''
                            COALESCE(SUM(\"vn_account_move_line\".balance), 0) AS balance,
                            COALESCE(SUM(\"vn_account_move_line\".amount_residual), 0) AS amount_residual,
                            COALESCE(SUM(\"vn_account_move_line\".debit), 0) AS debit,
                            COALESCE(SUM(\"vn_account_move_line\".credit), 0) AS credit
                        '''
            if currency_table:
                select = 'COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"vn_account_move_line\".company_currency_id = %s THEN ROUND(\"vn_account_move_line\".balance * %s, %s) '
                select += 'ELSE \"vn_account_move_line\".balance END), 0) AS balance, COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"vn_account_move_line\".company_currency_id = %s THEN ROUND(\"vn_account_move_line\".amount_residual * %s, %s) '
                select += 'ELSE \"vn_account_move_line\".amount_residual END), 0) AS amount_residual, COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"vn_account_move_line\".company_currency_id = %s THEN ROUND(\"vn_account_move_line\".debit * %s, %s) '
                select += 'ELSE \"vn_account_move_line\".debit END), 0) AS debit, COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"vn_account_move_line\".company_currency_id = %s THEN ROUND(\"vn_account_move_line\".credit * %s, %s) '
                select += 'ELSE \"vn_account_move_line\".credit END), 0) AS credit'
        # end logan
        else:

            select = '''
                COALESCE(SUM(\"account_move_line\".balance), 0) AS balance,
                COALESCE(SUM(\"account_move_line\".amount_residual), 0) AS amount_residual,
                COALESCE(SUM(\"account_move_line\".debit), 0) AS debit,
                COALESCE(SUM(\"account_move_line\".credit), 0) AS credit
            '''
            if currency_table:
                select = 'COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"account_move_line\".company_currency_id = %s THEN ROUND(\"account_move_line\".balance * %s, %s) '
                select += 'ELSE \"account_move_line\".balance END), 0) AS balance, COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"account_move_line\".company_currency_id = %s THEN ROUND(\"account_move_line\".amount_residual * %s, %s) '
                select += 'ELSE \"account_move_line\".amount_residual END), 0) AS amount_residual, COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"account_move_line\".company_currency_id = %s THEN ROUND(\"account_move_line\".debit * %s, %s) '
                select += 'ELSE \"account_move_line\".debit END), 0) AS debit, COALESCE(SUM(CASE '
                for currency_id, rate in currency_table.items():
                    extra_params += [currency_id, rate, decimal_places]
                    select += 'WHEN \"account_move_line\".company_currency_id = %s THEN ROUND(\"account_move_line\".credit * %s, %s) '
                select += 'ELSE \"account_move_line\".credit END), 0) AS credit'

        return select, extra_params

    def _eval_formula(self, financial_report, debit_credit, currency_table, linesDict_per_group, groups=False):
        groups = groups or {'fields': [], 'ids': [()]}
        debit_credit = debit_credit and financial_report.debit_credit
        formulas = self._split_formulas()
        currency = self.env.company.currency_id

        line_res_per_group = []

        if not groups['ids']:
            return [{'line': {'balance': 0.0}}]

        # this computes the results of the line itself
        for group_index, group in enumerate(groups['ids']):
            self_for_group = self.with_context(group_domain=self._get_group_domain(group, groups))
            linesDict = linesDict_per_group[group_index]
            line = False

            if self.code and self.code in linesDict and not self.need_recompute:
                line = linesDict[self.code]
            elif formulas and formulas['balance'].strip() == 'count_rows' and self.groupby:
                line_res_per_group.append({'line': {'balance': self_for_group._get_rows_count()}})
            elif formulas and formulas['balance'].strip() == 'from_context':
                line_res_per_group.append({'line': {'balance': self_for_group._get_value_from_context()}})
            else:
                line = FormulaLine(self_for_group, currency_table, financial_report, linesDict=linesDict)

            if line:
                res = {}
                res['balance'] = line.balance
                res['balance'] = currency.round(line.balance) if self.figure_type != 'percents' else line.balance
                if debit_credit:
                    res['credit'] = currency.round(line.credit)
                    res['debit'] = currency.round(line.debit)
                line_res_per_group.append(res)

        # don't need any groupby lines for count_rows and from_context formulas
        if all('line' in val for val in line_res_per_group):
            return line_res_per_group

        columns = []
        # this computes children lines in case the groupby field is set
        if self.domain and self.groupby and self.show_domain != 'never':
            # start logan
            is_our_vn_report = self.is_our_vn_report()
            if is_our_vn_report:
                if self.groupby not in self.env['vn.account.move.line']:
                    raise ValueError(_('Groupby should be a field from vn.account.move.line'))

                groupby = [self.groupby or 'id']
                if groups:
                    groupby = groups['fields'] + groupby
                groupby = ', '.join(['"vn_account_move_line".%s' % field for field in groupby])

                aml_obj = self.env['vn.account.move.line']
                tables, where_clause, where_params = aml_obj._query_get(domain=self._get_aml_domain())
                if financial_report.tax_report:
                    where_clause += ''' AND "vn_account_move_line".tax_exigible = 't' '''
            else:
                if self.groupby not in self.env['account.move.line']:
                    raise ValueError(_('Groupby should be a field from account.move.line'))

                groupby = [self.groupby or 'id']
                if groups:
                    groupby = groups['fields'] + groupby
                groupby = ', '.join(['"account_move_line".%s' % field for field in groupby])

                aml_obj = self.env['account.move.line']
                tables, where_clause, where_params = aml_obj._query_get(domain=self._get_aml_domain())
                if financial_report.tax_report:
                    where_clause += ''' AND "account_move_line".tax_exigible = 't' '''
            # end logan

            select, params = self._query_get_select_sum(currency_table)
            params += where_params

            sql, params = self._build_query_eval_formula(groupby, select, tables, where_clause, params)
            self.env.cr.execute(sql, params)
            results = self.env.cr.fetchall()
            for group_index, group in enumerate(groups['ids']):
                linesDict = linesDict_per_group[group_index]
                results_for_group = [result for result in results if group == result[:len(group)]]
                if results_for_group:
                    results_for_group = [r[len(group):] for r in results_for_group]
                    results_for_group = dict([(k[0], {'balance': k[1], 'amount_residual': k[2], 'debit': k[3], 'credit': k[4]}) for k in results_for_group])
                    c = FormulaContext(self.env['account.financial.html.report.line'].with_context(group_domain=self._get_group_domain(group, groups)),
                                       linesDict, currency_table, financial_report, only_sum=True)
                    if formulas:
                        for key in results_for_group:
                            c['sum'] = FormulaLine(results_for_group[key], currency_table, financial_report, type='not_computed')
                            c['sum_if_pos'] = FormulaLine(results_for_group[key]['balance'] >= 0.0 and results_for_group[key] or {'balance': 0.0},
                                                          currency_table, financial_report, type='not_computed')
                            c['sum_if_neg'] = FormulaLine(results_for_group[key]['balance'] <= 0.0 and results_for_group[key] or {'balance': 0.0},
                                                          currency_table, financial_report, type='not_computed')
                            for col, formula in formulas.items():
                                if col in results_for_group[key]:
                                    results_for_group[key][col] = safe_eval(formula, c, nocopy=True)
                    to_del = []
                    for key in results_for_group:
                        if self.env.company.currency_id.is_zero(results_for_group[key]['balance']):
                            to_del.append(key)
                    for key in to_del:
                        del results_for_group[key]
                    results_for_group.update({'line': line_res_per_group[group_index]})
                    columns.append(results_for_group)
                else:
                    res_vals = {'balance': 0.0}
                    if debit_credit:
                        res_vals.update({'debit': 0.0, 'credit': 0.0})
                    columns.append({'line': res_vals})

        return columns or [{'line': res} for res in line_res_per_group]

    # @profile(immediate=True)
    def _get_lines(self, financial_report, currency_table, options, linesDicts):
        _logger.error("_get_lines")
        # update res partner
        list_partner = []
        if self.is_our_vn_report():
            if 'date' in options:
                if 'date_from' in options.get('date'):
                    check_date_from = datetime.strptime(options.get('date')['date_from'], '%Y-%m-%d').date()
                    check_date_to = datetime.strptime(options.get('date')['date_to'], '%Y-%m-%d').date()
                    read = None
                    if self.is_our_vn_report() != 1:
                        read = self.env['account.move.line'].sudo().read_group([('date', '>=', check_date_from), ('date', '<=', check_date_to)], ['partner_id'], 'partner_id',
                                                                               lazy=False)
                    else:
                        read = self.env['account.move.line'].sudo().read_group([('date', '<=', check_date_to)], ['partner_id'], 'partner_id', lazy=False)
                        if not financial_report.is_compute_dn_01_account_balance_positive:
                            # update dn_01_balance_positive
                            self.env['account.account'].search([])._compute_dn_01_balance_positive(date_to=check_date_to)
                            financial_report.is_compute_dn_01_account_balance_positive = True

                        if not financial_report.is_compute_vn_date_due_remain:
                            today_365 = check_date_to + timedelta(days=365)
                            self.env.cr.execute("""update vn_account_move_line set date_maturity_short=True where date_maturity is NULL or date_maturity <= %s""", (today_365,))
                            self.env.cr.execute("""update vn_account_move_line set date_maturity_short=False where date_maturity is not NULL and date_maturity > %s""", (today_365,))
                            today_90 = check_date_to + timedelta(days=90)
                            self.env.cr.execute("""update vn_account_move_line set date_maturity_3_short=True where date_maturity is NULL or date_maturity <= %s""", (today_90,))
                            self.env.cr.execute("""update vn_account_move_line set date_maturity_3_short=False where date_maturity is not NULL and date_maturity > %s""", (today_90,))
                            financial_report.is_compute_vn_date_due_remain = True
                    if read:
                        for rec in read:
                            if rec['partner_id']:
                                if rec['partner_id'][0] not in list_partner:
                                    list_partner.append(rec['partner_id'][0])
                    partners = self.env['res.partner'].sudo().search([('id', 'in', list_partner)])
                    if partners:
                        partners._compute_vn_inter_balance(date_from=check_date_from, date_to=check_date_to)
        # update vals insert domain
        final_result_table = []
        comparison_table = [options.get('date')]
        comparison_table += options.get('comparison') and options['comparison'].get('periods', []) or []
        currency_precision = self.env.company.currency_id.rounding

        count = 0
        if not financial_report.is_compute_dn_01_account_balance_compare_positive:
            for period in comparison_table:
                count += 1
                date_to = period.get('date_to', False) or period.get('date', False)
                if count == 2:
                    # update dn_01_balance_positive
                    self.env['account.account'].search([])._compute_dn_01_balance_compare_positive(date_to=date_to)
                    financial_report.is_compute_dn_01_account_balance_compare_positive = True
        # compute vn compare
        count = 0
        if not financial_report.is_compute_vn_date_due_compare_remain:
            for period in comparison_table:
                count += 1
                date_to = period.get('date_to', False) or period.get('date', False)
                if count == 2:
                    # update dn_01_date_maturity
                    date_to_date = datetime.strptime(date_to, '%Y-%m-%d')
                    today_365 = date_to_date + timedelta(days=365)
                    self.env.cr.execute("""update vn_account_move_line set date_maturity_compare_short=True where date_maturity is NULL or date_maturity <= %s""", (today_365,))
                    self.env.cr.execute("""update vn_account_move_line set date_maturity_compare_short=False where date_maturity is not NULL and date_maturity > %s""", (today_365,))
                    today_90 = date_to_date + timedelta(days=90)
                    self.env.cr.execute("""update vn_account_move_line set date_maturity_3_compare_short=True where date_maturity is NULL or date_maturity <= %s""", (today_90,))
                    self.env.cr.execute("""update vn_account_move_line set date_maturity_3_compare_short=False where date_maturity is not NULL and date_maturity > %s""", (today_90,))
                    financial_report.is_compute_vn_date_due_compare_remain = True
                    # update ngan han, dai han
                    self.env['res.partner'].sudo().search([('id', 'in', list_partner)])._compute_vn_inter_compare_balance(date_to=date_to_date.date())
                # build comparison table
        for line in self:
            res = []
            debit_credit = len(comparison_table) == 1
            domain_ids = {'line'}
            k = 0
            domain_backup = None
            # show_domain_backup = None
            count = 0
            for period in comparison_table:
                count += 1
                date_from = period.get('date_from', False)
                date_to = period.get('date_to', False) or period.get('date', False)
                date_from, date_to, strict_range = line.with_context(date_from=date_from, date_to=date_to)._compute_date_range()

                if count == 1:
                    a = 0
                else:
                    # start backup domain
                    if not domain_backup:
                        domain_backup = {}
                        for line_test in self:
                            domain_backup[line_test.id] = line_test.domain
                    for line_test in self:
                        if line_test.domain and (
                                'dn_01_balance_positive' in line_test.domain or
                                'date_maturity_short' in line_test.domain or
                                'partner_id_balance_b01_131_short_positive' in line_test.domain or
                                'partner_id_balance_b01_211_long_positive' in line_test.domain or
                                'partner_id_balance_b01_311_short_positive' in line_test.domain or
                                'partner_id_balance_b01_331_long_positive' in line_test.domain or
                                'partner_id_balance_b01_132_short_positive' in line_test.domain or
                                'partner_id_balance_b01_132_long_positive' in line_test.domain or
                                'partner_id_balance_b01_136_positive' in line_test.domain or
                                'partner_id_balance_b01_139_positive' in line_test.domain or
                                'partner_id_balance_b01_215_positive' in line_test.domain or
                                'partner_id_balance_b01_153_positive' in line_test.domain or
                                'partner_id_balance_b01_216_positive' in line_test.domain or
                                'partner_id_balance_b01_313_positive' in line_test.domain or
                                'partner_id_balance_b01_314_positive' in line_test.domain or
                                'partner_id_balance_b01_318_positive' in line_test.domain or
                                'partner_id_balance_b01_319_positive' in line_test.domain or
                                'partner_id_balance_b01_336_positive' in line_test.domain or
                                'partner_id_balance_b01_337_positive' in line_test.domain
                        ):
                            new_domain_test = line_test.domain
                            new_domain_test = new_domain_test.replace('dn_01_balance_positive', 'dn_01_balance_compare_positive')
                            new_domain_test = new_domain_test.replace('date_maturity_short', 'date_maturity_compare_short')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_131_short_positive', 'partner_id_balance_b01_131_short_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_211_long_positive', 'partner_id_balance_b01_211_long_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_311_short_positive', 'partner_id_balance_b01_311_short_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_331_long_positive', 'partner_id_balance_b01_331_long_compare_positive')

                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_132_short_positive', 'partner_id_balance_b01_132_short_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_132_long_positive', 'partner_id_balance_b01_132_long_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_136_positive', 'partner_id_balance_b01_136_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_139_positive', 'partner_id_balance_b01_139_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_215_positive', 'partner_id_balance_b01_215_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_153_positive', 'partner_id_balance_b01_153_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_216_positive', 'partner_id_balance_b01_216_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_313_positive', 'partner_id_balance_b01_313_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_314_positive', 'partner_id_balance_b01_314_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_318_positive', 'partner_id_balance_b01_318_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_319_positive', 'partner_id_balance_b01_319_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_336_positive', 'partner_id_balance_b01_336_compare_positive')
                            new_domain_test = new_domain_test.replace('partner_id_balance_b01_337_positive', 'partner_id_balance_b01_337_compare_positive')
                            line_test.update({
                                'domain': new_domain_test
                            })

                r = line.with_context(date_from=date_from,
                                      date_to=date_to,
                                      strict_range=strict_range)._eval_formula(financial_report,
                                                                               debit_credit,
                                                                               currency_table,
                                                                               linesDicts[k],
                                                                               groups=options.get('groups'))

                debit_credit = False
                res.extend(r)
                for column in r:
                    domain_ids.update(column)
                k += 1

            res = line._put_columns_together(res, domain_ids)

            if line.hide_if_zero and all([float_is_zero(k, precision_rounding=currency_precision) for k in res['line']]):
                continue

            # logan hide if negative positive
            if line.hide_if_negative:
                new_res_line = []
                count = 0
                for res_line_item in res['line']:
                    count += 1
                    if res_line_item < 0:
                        res_line_item = 0
                        # if count == 1:
                        #     show_domain_backup = line.show_domain
                        #     line.show_domain = 'never'
                    new_res_line.append(res_line_item)
                res['line'] = new_res_line
            if line.hide_if_positive and all([k > 0 for k in res['line']]):
                continue

            # logan end hide if negative positive

            # Post-processing ; creating line dictionnary, building comparison, computing total for extended, formatting
            vals = {
                'id': line.id,
                'domain': line.domain,
                'name': line.name,
                'level': line.level,
                'class': 'o_account_reports_totals_below_sections' if self.env.company.totals_below_sections else '',
                'columns': [{'name': l} for l in res['line']],
                'unfoldable': len(domain_ids) > 1 and line.show_domain != 'always',
                'unfolded': line.id in options.get('unfolded_lines', []) or line.show_domain == 'always',
                'page_break': line.print_on_new_page,
            }

            if financial_report.tax_report and line.domain and not line.action_id:
                vals['caret_options'] = 'tax.report.line'

            if line.action_id:
                vals['action_id'] = line.action_id.id
            domain_ids.remove('line')
            lines = [vals]
            groupby = line.groupby or 'aml'
            if line.id in options.get('unfolded_lines', []) or line.show_domain == 'always':
                if line.groupby:
                    domain_ids = sorted(list(domain_ids), key=lambda k: line._get_gb_name(k))
                for domain_id in domain_ids:
                    name = line._get_gb_name(domain_id)
                    if not self.env.context.get('print_mode') or not self.env.context.get('no_format'):
                        name = name[:40] + '...' if name and len(name) >= 45 else name
                    vals = {
                        'id': domain_id,
                        'domain': line.domain,
                        'name': name,
                        'level': line.level,
                        'parent_id': line.id,
                        'columns': [{'name': l} for l in res[domain_id]],
                        'caret_options': groupby == 'account_id' and 'account.account' or groupby,
                        'financial_group_line_id': line.id,
                    }
                    if line.financial_report_id.name == 'Aged Receivable':
                        vals['trust'] = self.env['res.partner'].browse([domain_id]).trust
                    lines.append(vals)
                if domain_ids and self.env.company.totals_below_sections:
                    lines.append({
                        'id': 'total_' + str(line.id),
                        'domain': line.domain,
                        'name': _('Total') + ' ' + line.name,
                        'level': line.level,
                        'class': 'o_account_reports_domain_total',
                        'parent_id': line.id,
                        'columns': copy.deepcopy(lines[0]['columns']),
                    })

            for vals in lines:
                if len(comparison_table) == 2 and not options.get('groups'):
                    vals['columns'].append(line._build_cmp(vals['columns'][0]['name'], vals['columns'][1]['name']))
                    for i in [0, 1]:
                        vals['columns'][i] = line._format(vals['columns'][i])
                else:
                    vals['columns'] = [line._format(v) for v in vals['columns']]
                if not line.formulas:
                    vals['columns'] = [{'name': ''} for k in vals['columns']]

            if len(lines) == 1:
                new_lines = line.children_ids._get_lines(financial_report, currency_table, options, linesDicts)
                if new_lines and line.formulas:
                    if self.env.company.totals_below_sections:
                        divided_lines = self._divide_line(lines[0])
                        result = [divided_lines[0]] + new_lines + [divided_lines[-1]]
                    else:
                        result = [lines[0]] + new_lines
                else:
                    if not new_lines and not lines[0]['unfoldable'] and line.hide_if_empty:
                        lines = []
                    result = lines + new_lines
            else:
                result = lines
            final_result_table += result

            # re update old domain
            # if show_domain_backup:
            #     line.show_domain = show_domain_backup
            if domain_backup:
                for line_test in self:
                    line_test.update({
                        'domain': domain_backup[line_test.id]
                    })

        _logger.error("end _get_lines")
        return final_result_table


class FormulaLine(object):
    def __init__(self, obj, currency_table, financial_report, type='balance', linesDict=None):
        if linesDict is None:
            linesDict = {}
        fields = dict((fn, 0.0) for fn in ['debit', 'credit', 'balance'])
        if type == 'balance':
            fields = obj._get_balance(linesDict, currency_table, financial_report)[0]
            linesDict[obj.code] = self
        elif type in ['sum', 'sum_if_pos', 'sum_if_neg']:
            if type == 'sum_if_neg':
                obj = obj.with_context(sum_if_neg=True)
            if type == 'sum_if_pos':
                obj = obj.with_context(sum_if_pos=True)
            if obj._name == 'account.financial.html.report.line':
                fields = obj._get_sum(currency_table, financial_report)
                self.amount_residual = fields['amount_residual']
            elif obj._name == 'account.move.line':
                self.amount_residual = 0.0
                field_names = ['debit', 'credit', 'balance', 'amount_residual']
                res = obj.env['account.financial.html.report.line']._compute_line(currency_table, financial_report)
                for field in field_names:
                    fields[field] = res[field]
                self.amount_residual = fields['amount_residual']
        elif type == 'not_computed':
            for field in fields:
                fields[field] = obj.get(field, 0)
            self.amount_residual = obj.get('amount_residual', 0)
        elif type == 'null':
            self.amount_residual = 0.0
        self.balance = fields['balance']
        self.credit = fields['credit']
        self.debit = fields['debit']


class FormulaContext(dict):
    def __init__(self, reportLineObj, linesDict, currency_table, financial_report, curObj=None, only_sum=False, *data):
        self.reportLineObj = reportLineObj
        self.curObj = curObj
        self.linesDict = linesDict
        self.currency_table = currency_table
        self.only_sum = only_sum
        self.financial_report = financial_report
        return super(FormulaContext, self).__init__(data)

    def __getitem__(self, item):
        formula_items = ['sum', 'sum_if_pos', 'sum_if_neg']
        if item in set(__builtins__.keys()) - set(formula_items):
            return super(FormulaContext, self).__getitem__(item)

        if self.only_sum and item not in formula_items:
            return FormulaLine(self.curObj, self.currency_table, self.financial_report, type='null')
        if self.get(item):
            return super(FormulaContext, self).__getitem__(item)
        if self.linesDict.get(item):
            return self.linesDict[item]
        if item == 'sum':
            res = FormulaLine(self.curObj, self.currency_table, self.financial_report, type='sum')
            self['sum'] = res
            return res
        if item == 'sum_if_pos':
            res = FormulaLine(self.curObj, self.currency_table, self.financial_report, type='sum_if_pos')
            self['sum_if_pos'] = res
            return res
        if item == 'sum_if_neg':
            res = FormulaLine(self.curObj, self.currency_table, self.financial_report, type='sum_if_neg')
            self['sum_if_neg'] = res
            return res
        if item == 'NDays':
            d1 = fields.Date.from_string(self.curObj.env.context['date_from'])
            d2 = fields.Date.from_string(self.curObj.env.context['date_to'])
            res = (d2 - d1).days
            self['NDays'] = res
            return res
        if item == 'count_rows':
            return self.curObj._get_rows_count()
        if item == 'from_context':
            return self.curObj._get_value_from_context()
        line_id = self.reportLineObj.search([('code', '=', item)], limit=1)
        if line_id:
            date_from, date_to, strict_range = line_id._compute_date_range()
            res = FormulaLine(line_id.with_context(strict_range=strict_range, date_from=date_from, date_to=date_to), self.currency_table, self.financial_report, linesDict=self.linesDict)
            self.linesDict[item] = res
            return res
        return super(FormulaContext, self).__getitem__(item)
