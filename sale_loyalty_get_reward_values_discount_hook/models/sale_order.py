# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, models
from odoo.fields import Command


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
        return {
            "name": _(
                "Discount: %(desc)s%(tax_str)s",
                desc=reward.description,
                tax_str=tax_desc,
            ),
            "product_id": reward_product.id,
            "price_unit": -(price * discount_factor),
            "product_uom_qty": 1.0,
            "product_uom": reward_product.uom_id.id,
            "reward_id": reward.id,
            "coupon_id": coupon.id,
            "points_cost": 0,
            "reward_identifier_code": reward_code,
            "sequence": sequence,
            "tax_id": [Command.clear()]
            + [Command.link(tax.id) for tax in mapped_taxes],
        }
