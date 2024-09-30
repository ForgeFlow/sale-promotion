# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _reward_by_tax(
        self,
        tax,
        tax_desc,
        reward,
        reward_product,
        price,
        discount_factor,
        coupon,
        reward_code,
        sequence,
        mapped_taxes,
    ):
        res = super()._reward_by_tax(
            tax,
            tax_desc,
            reward,
            reward_product,
            price,
            discount_factor,
            coupon,
            reward_code,
            sequence,
            mapped_taxes,
        )
        reward_product = self.get_reward_product_by_tax(tax)
        if reward_product:
            res["product_id"] = reward_product
        return res

    def get_reward_product_by_tax(self, tax):
        reward_product_tax = self.env["loyalty.reward.tax.product"].search(
            [("tax_id", "=", tax.id)], limit=1
        )
        if reward_product_tax:
            return reward_product_tax.product_id.id
        else:
            coupons_tax_code = self.env["product.tax.code"].search(
                [("name", "=", "OC030000")]
            )
            product = self.env["product.product"].create(
                {
                    "name": "Discount %s" % tax.display_name,
                    "type": "service",
                    "tax_code_id": coupons_tax_code.id if coupons_tax_code else False,
                }
            )
            self.env["loyalty.reward.tax.product"].create(
                {"name": tax.display_name, "product_id": product.id, "tax_id": tax.id}
            )
            return product.id
        return False

    # TODO: this skips the tax computing on reward lines
    # def _avatax_prepare_lines(self, order_lines, doc_type=None):
    #     lines = super()._avatax_prepare_lines(order_lines, doc_type=doc_type)
    #     lines = [
    #         line._avatax_prepare_line(sign=1, doc_type=doc_type)
    #         for line in order_lines.filtered(
    #             lambda line: not line.display_type and not line.is_reward_line
    #         )
    #     ]
    #     return [x for x in lines if x]

    def action_confirm(self):
        avatax_config = self.company_id.get_avatax_config_company()
        if avatax_config:
            # apply promotion after recomputing taxes
            if any(sol.is_reward_line for sol in self.order_line):
                self._update_programs_and_rewards()
        res = super(SaleOrder, self).action_confirm()
        return res
