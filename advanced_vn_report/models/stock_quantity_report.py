from odoo import fields, models, api


class StockQuantityReport(models.Model):
    _name = 'stock.quantity.report'
    _description = 'Báo cáo xuất nhập tồn'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)
    name = fields.Char()
    date_from = fields.Date(string='Từ ngày ')
    date_to = fields.Date(string='Đến ngày')
    location_id = fields.Many2one(comodel_name='stock.location', string='kho', required=False)
    line_ids = fields.One2many('stock.quantity.report.line', 'stock_quantity_report_id', string='Báo cáo')

    def load_data(self):
        for rec in self:
            date_from = rec.date_from
            date_to = rec.date_to
            location_id = rec.location_id.id
            sml_start = rec.env['stock.move.line'].sudo().search(
                ['|', ('location_dest_id', '=', location_id),
                 ('location_id', '=', location_id)])
            line_list = []
            product_list = []
            for sml in sml_start:
                if sml.product_id in product_list:
                    pass
                else:
                    product_list.append(sml.product_id)
            for product in product_list:
                #Tìm các stock move line nhập trước thời điểm lựa chọn ( tồn đầu kì )
                # sml_start_in = rec.env['stock.move.line'].sudo().search(
                #     [('create_date', '<', date_from),
                #      ('location_dest_id', '=', location_id),
                #      ('product_id', '=', product.id)])
                # # Tìm các stock move line xuất trước thời điểm lựa chọn ( tồn đầu kì )
                # sml_start_out = rec.env['stock.move.line'].sudo().search(
                #     [('create_date', '<', date_from),
                #      ('location_id', '=', location_id),
                #      ('product_id', '=', product.id)])
                # sml_qty_start_in = 0 #số lượng nhập đầu kì
                # sml_qty_start_out = 0 #số lượng xuất đầu kì
                # sml_value_start_in = 0 #thành tiền nhập đầu kì
                # sml_value_start_out = 0 #thành tiền xuất đầu kì
                sml_qty_in = 0 #số lượng nhập trong kì
                sml_qty_out = 0 #số lượng xuất trong kì
                sml_value_in = 0 #thành tiền nhập trong kì
                sml_value_out = 0 #thành tiền nhập trong kì
                sml_qty_start = product.with_context(location=location_id, to_date=date_from).qty_available
                svl_start = rec.env['stock.valuation.layer'].sudo().search(
                    [('create_date', '<', date_from),
                     ('product_id', '=', product.id)])
                svl_start_qty = sum([line.quantity for line in svl_start])
                svl_start_value = sum([line.value for line in svl_start])
                svl_price_unit = 0
                if svl_start_qty != 0:
                    svl_price_unit = svl_start_value/svl_start_qty
                sml_value_start = svl_price_unit * sml_qty_start
                # for sml_id in sml_start_in:
                #     qty = sml_id.qty_done
                #     qty_total = sum([line.qty_done for line in sml_id.move_id.move_line_ids])
                #     value_total = sum([line.amount_total_signed for line in sml_id.move_id.account_move_ids])
                #     #tính thành tiền nhập theo công thức giá tiền (lấy từ account move) chia tổng số lượng ở stock move
                #     #nhân với số lược ở move line hiện tại( do 1 stock move có thể có nhiều stock move line đến kho khác)
                #     sml_value_start_in += value_total / qty_total * qty
                #     sml_qty_start_in += qty #cập nhật tổn số lượng nhập
                # for sml_id in sml_start_out:
                #     qty = sml_id.qty_done
                #     qty_total = sum([line.qty_done for line in sml_id.move_id.move_line_ids])
                #     value_total = sum([line.amount_total_signed for line in sml_id.move_id.account_move_ids])
                #     sml_value_start_out += value_total / qty_total * qty
                #     sml_qty_start_out += qty
                # #Tổn đầu kỳ = nhập đầu kỳ - xuất đầu kỳ
                # sml_qty_start = sml_qty_start_in - sml_qty_start_out
                # sml_value_start = sml_value_start_in - sml_value_start_out
                # Tìm các stock move line nhập trong thời điểm lựa chọn ( nhập trong kì )
                sml_in = rec.env['stock.move.line'].sudo().search(
                    [('create_date', '>=', date_from),
                     ('create_date', '<=', date_to),
                     ('location_dest_id', '=', location_id),
                     ('product_id', '=', product.id)])
                # Tìm các stock move line xuất trong thời điểm lựa chọn ( xuất trong kì )
                sml_out = rec.env['stock.move.line'].sudo().search(
                    [('create_date', '>=', date_from),
                     ('create_date', '<=', date_to),
                     ('location_id', '=', location_id),
                     ('product_id', '=', product.id)])
                for sml_id in sml_in:
                    qty = sml_id.qty_done
                    qty_total = sum([line.qty_done for line in sml_id.move_id.move_line_ids])
                    value_total = sum([line.amount_total_signed for line in sml_id.move_id.account_move_ids])
                    sml_value_in += value_total / qty_total * qty
                    sml_qty_in += qty
                for sml_id in sml_out:
                    qty = sml_id.qty_done
                    qty_total = sum([line.qty_done for line in sml_id.move_id.move_line_ids])
                    value_total = sum([line.amount_total_signed for line in sml_id.move_id.account_move_ids])
                    sml_value_out += value_total / qty_total * qty
                    sml_qty_out += qty
                # tồn cuối kỳ = tồn đầu kỳ + nhập trong kỳ - xuất trong kỳ
                sml_qty_end = sml_qty_start + sml_qty_in - sml_qty_out
                sml_value_end = sml_value_start + sml_value_in - sml_value_out
                line = {
                    'product_id': product.product_tmpl_id.id,
                    'default_code': product.default_code,
                    'uom_id': product.uom_id.id,
                    'product_qty_start': sml_qty_start,
                    'value_start': sml_value_start,
                    'product_qty_end': sml_qty_end,
                    'value_end': sml_value_end,
                    'product_qty_in': sml_qty_in,
                    'value_in': sml_value_in,
                    'product_qty_out': sml_qty_out,
                    'value_out': sml_value_out,
                }
                line_list.append(line)
            rec.line_ids = [(5, 0, 0)]
            rec.line_ids = [(0, 0, value) for value in line_list]
