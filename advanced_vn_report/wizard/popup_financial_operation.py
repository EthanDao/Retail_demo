from datetime import datetime, time

from odoo import fields, models, api


class PopupFinancialOperation(models.Model):
    _name = 'popup.financial.operation'
    _description = 'Description'

    date_from = fields.Date(string='Từ ngày', default='2020-01-01')
    date_to = fields.Date(string='Đến ngày',  default='2020-12-31')
    name = fields.Char()

    # @api.model
    # def _get_default_financial_operation_id(self):
    #     if self._context.get('active_ids'):
    #         return self.env['financial.operation'].browse(self._context.get('active_ids'))

    financial_operation_id = fields.Many2one('financial.operation', string="Thuyết minh tài chính")

    # financial_value = fields.Char(
    #     string='Giá trị',
    #     required=False)

    def button_compute_sum_financial(self):
        data = {}
        date_from = None
        date_to = None
        if self.date_from and self.date_to:
            date_from = datetime.combine(self.date_from, time(0, 0))
            date_to = datetime.combine(self.date_to, time(0, 0))
        # financial = self.env['financial.operation'].sudo().search([], limit=1)
        financial = self.env['financial.note'].sudo().search([], limit=1)
        if financial:
            financial_lines = self.env['financial.config.line'].sudo().search(
                [('financial_note_id', '=', financial.id)])
            if len(financial_lines) > 0:
                for line in financial_lines:
                    line_data = line.compute_line(date_from=date_from, date_to=date_to)
                    # if len(line_data) > 0 and type(line_data[0][1]) != str and int(line_data[0][1]) > 0:
                    #     print(line.name)
                    #     print(line_data)
                    for dt in line_data:
                        data.update({
                            dt[0]: dt[1]
                        })
        if len(data) > 0:
            col_rows_financial = None
            if self.financial_operation_id:
                col_rows_financial = str(self.financial_operation_id.col) + str(self.financial_operation_id.row)
            for key in data:
                if key == col_rows_financial:
                    print(key)
                    print(col_rows_financial)
                    print('{:,.2f}'.format(data[key]))
                    self.financial_operation_id.financial_value = '{:,.2f}'.format(data[key])
        # if self.financial_operation_id:
        #     # financial_lines = self.env['financial.config.line'].sudo().search(
        #     #     [('financial_note_id', '=', financial.id)])
        #     if self.financial_operation_id.operation_lines:
        #         for line in self.financial_operation_id.operation_lines:
        #             if len(line) > 0:
        #     # if len(financial_lines) > 0:
        #     #     for line in financial_lines:
        #                 line_data = line.compute_line(date_from=date_from, date_to=date_to)
        #                 if len(line_data) > 0 and type(line_data[0][1]) != str and int(line_data[0][1]) > 0:
        #                     print(line.name)
        #                     print(line_data)
        #                 for dt in line_data:
        #                     data.update({
        #                         dt[0]: dt[1]
        #                     })
        # for dt in line_data:
        #     data.update({
        #         dt[0]: dt[1]
        #     })
        # financial_operation = self.env['financial.operation'].search([])
        # if self.financial_operation_id:
        #     if self.financial_operation_id.operation_lines:
        #         for line in self.financial_operation_id.operation_lines:
        #             date_form, date_to, value = line.compute_line()
