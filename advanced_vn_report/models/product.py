from odoo import models, api, _


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _prepare_internal_svl_vals(self, quantity, unit_cost):
        self.ensure_one()
        vals = {
            "product_id": self.id,
            "value": unit_cost * quantity,
            "unit_cost": unit_cost,
            "quantity": quantity,
        }
        if self.cost_method in ("average", "fifo"):
            vals["remaining_qty"] = quantity
            vals["remaining_value"] = vals["value"]
        return vals


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def update_product(self):
        sql = """UPDATE product_template SET type ='product' WHERE type='consu'"""
        self._cr.execute(sql)

    def write(self, vals):
        impacted_templates = {}
        move_vals_list = []
        Product = self.env['product.product']
        SVL = self.env['stock.valuation.layer']

        if 'categ_id' in vals:
            # When a change of category implies a change of cost method, we empty out and replenish
            # the stock.
            new_product_category = self.env['product.category'].browse(vals.get('categ_id'))

            for product_template in self:
                valuation_impacted = False
                if product_template.cost_method != new_product_category.property_cost_method:
                    valuation_impacted = True
                if product_template.valuation != new_product_category.property_valuation:
                    valuation_impacted = True
                if valuation_impacted is False:
                    continue

                # Empty out the stock with the current cost method.
                description = _("Due to a change of product category (from %s to %s), the costing method\
                                has changed for product template %s: from %s to %s.") % \
                              (product_template.categ_id.display_name, new_product_category.display_name, \
                               product_template.display_name, product_template.cost_method,
                               new_product_category.property_cost_method)
                out_svl_vals_list, products_orig_quantity_svl, products = Product._svl_empty_stock(description,
                                                                                                   product_template=product_template)
                if out_svl_vals_list:
                    out_svl_vals_list[0].update({
                        'is_change_product_category': True
                    })
                    out_stock_valuation_layers = SVL.create(out_svl_vals_list)
                    if product_template.valuation == 'real_time':
                        move_vals_list += Product._svl_empty_stock_am(out_stock_valuation_layers)
                    impacted_templates[product_template] = (products, description, products_orig_quantity_svl)

        res = super(ProductTemplate, self).write(vals)

        for product_template, (products, description, products_orig_quantity_svl) in impacted_templates.items():
            # Replenish the stock with the new cost method.
            in_svl_vals_list = products._svl_replenish_stock(description, products_orig_quantity_svl)
            in_svl_vals_list[0].update({
                'is_change_product_category': True
            })
            in_stock_valuation_layers = SVL.create(in_svl_vals_list)
            if product_template.valuation == 'real_time':
                move_vals_list += Product._svl_replenish_stock_am(in_stock_valuation_layers)

        # Create the account moves.
        if move_vals_list:
            account_moves = self.env['account.move'].create(move_vals_list)
            account_moves.post()
        return res
