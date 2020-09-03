from odoo import models, api, fields


class Picking(models.Model):
    _inherit = "stock.picking"
    allow_product_ids = fields.Many2many('product.product')
    sale_order_id = fields.Many2one('sale.order', string='Đơn hàng')
    is_nhap_kho_nguyen_lieu_thua = fields.Boolean(string='Là nhập kho nguyên liệu thừa', default=False)
    def button_validate(self):
        res = super(Picking, self).button_validate()
        # cap nhat hop dong cho stock move, account move va account move line
        if self.sale_order_id:
            # self.move_lines.sudo().update({
            #     'sale_order_contract_id': self.sale_order_id.contract_id.id
            # })
            for move in self.move_lines:
                for account_move in move.account_move_ids:
                    account_move.sudo().update({
                        # 'sale_order_contract_id': self.sale_order_id.contract_id.id,
                        'account_contract_id': self.sale_order_id.contract_id.account_contract_id.id
                    })
                    for line in account_move.line_ids:
                        line.sudo().update({
                            'account_contract_id': self.sale_order_id.contract_id.account_contract_id.id
                        })
        if self.is_nhap_kho_nguyen_lieu_thua:
            # danh dau cac stock move, account move va account move line la nhap kho nguyen vat lieu
            if self.is_nhap_kho_nguyen_lieu_thua:
                self.move_lines.sudo().update({
                    'value_deduction': True
                })
                for move in self.move_lines:
                    for account_move in move.account_move_ids:
                        account_move.sudo().update({
                            'value_deduction': True
                        })
        return res

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    allow_product_ids = fields.Many2many('product.product', related='picking_id.allow_product_ids')

    @api.onchange('allow_product_ids')
    def check_onchange_allow_product_ids(self):
        if len(self.allow_product_ids.ids) > 0:
            return {
                'domain': {
                    'product_id': [('id', 'in', self.allow_product_ids.ids)]
                }
            }

