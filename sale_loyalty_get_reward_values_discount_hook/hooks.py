# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import random
from collections import defaultdict

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.fields import Command

from odoo.addons.sale_loyalty.models.sale_order import SaleOrder


def _generate_random_reward_code():
    return str(random.getrandbits(32))


def post_load_hook():

    # Changes done to the original method are highlighted with the comments
    # "START/END HOOK"
    # flake8: noqa: C901
    def _new_get_reward_values_discount(self, reward, coupon, **kwargs):
        self.ensure_one()
        assert reward.reward_type == "discount"

        # Figure out which lines are concerned by the discount
        # cheapest_line = self.env['sale.order.line']
        discountable = 0
        discountable_per_tax = defaultdict(int)
        reward_applies_on = reward.discount_applicability
        sequence = (
            max(
                self.order_line.filtered(lambda x: not x.is_reward_line).mapped(
                    "sequence"
                ),
                default=10,
            )
            + 1
        )
        if reward_applies_on == "order":
            discountable, discountable_per_tax = self._discountable_order(reward)
        elif reward_applies_on == "specific":
            discountable, discountable_per_tax = self._discountable_specific(reward)
        elif reward_applies_on == "cheapest":
            discountable, discountable_per_tax = self._discountable_cheapest(reward)
        if not discountable:
            if not reward.program_id.is_payment_program and any(
                line.reward_id.program_id.is_payment_program for line in self.order_line
            ):
                return [
                    {
                        "name": _("TEMPORARY DISCOUNT LINE"),
                        "product_id": reward.discount_line_product_id.id,
                        "price_unit": 0,
                        "product_uom_qty": 0,
                        "product_uom": reward.discount_line_product_id.uom_id.id,
                        "reward_id": reward.id,
                        "coupon_id": coupon.id,
                        "points_cost": 0,
                        "reward_identifier_code": _generate_random_reward_code(),
                        "sequence": sequence,
                        "tax_id": [(Command.CLEAR, 0, 0)],
                    }
                ]
            raise UserError(_("There is nothing to discount"))
        max_discount = reward.currency_id._convert(
            reward.discount_max_amount,
            self.currency_id,
            self.company_id,
            fields.Date.today(),
        ) or float("inf")
        # discount should never surpass the order's current total amount
        max_discount = min(self.amount_total, max_discount)
        if reward.discount_mode == "per_point":
            points = self._get_real_points_for_coupon(coupon)
            if not reward.program_id.is_payment_program:
                # Rewards cannot be partially offered to customers
                points = points // reward.required_points * reward.required_points
            max_discount = min(
                max_discount,
                reward.currency_id._convert(
                    reward.discount * points,
                    self.currency_id,
                    self.company_id,
                    fields.Date.today(),
                ),
            )
        elif reward.discount_mode == "per_order":
            max_discount = min(
                max_discount,
                reward.currency_id._convert(
                    reward.discount,
                    self.currency_id,
                    self.company_id,
                    fields.Date.today(),
                ),
            )
        elif reward.discount_mode == "percent":
            max_discount = min(max_discount, discountable * (reward.discount / 100))
        # Discount per taxes
        reward_code = _generate_random_reward_code()
        point_cost = (
            reward.required_points
            if not reward.clear_wallet
            else self._get_real_points_for_coupon(coupon)
        )
        if reward.discount_mode == "per_point" and not reward.clear_wallet:
            # Calculate the actual point cost if the cost is per point
            converted_discount = self.currency_id._convert(
                min(max_discount, discountable),
                reward.currency_id,
                self.company_id,
                fields.Date.today(),
            )
            point_cost = converted_discount / reward.discount
        # Gift cards and eWallets are considered gift cards and should not have any taxes
        if reward.program_id.is_payment_program:
            reward_product = reward.discount_line_product_id
            reward_line_values = {
                "name": reward.description,
                "product_id": reward_product.id,
                "price_unit": -min(max_discount, discountable),
                "product_uom_qty": 1.0,
                "product_uom": reward_product.uom_id.id,
                "reward_id": reward.id,
                "coupon_id": coupon.id,
                "points_cost": point_cost,
                "reward_identifier_code": reward_code,
                "sequence": sequence,
                "tax_id": [Command.clear()],
            }
            if reward.program_id.program_type == "gift_card":
                # For gift cards, the SOL should consider the discount product taxes
                # TODO VFE in 16.4+, use dedicated API of tax filtering
                taxes_to_apply = reward_product.taxes_id.filtered(
                    lambda tax: tax.company_id.id == self.company_id.id
                )
                if taxes_to_apply:
                    mapped_taxes = self.fiscal_position_id.map_tax(taxes_to_apply)
                    price_incl_taxes = mapped_taxes.filtered("price_include")
                    tax_res = mapped_taxes.with_context(
                        force_price_include=True,
                        round=False,
                        round_base=False,
                    ).compute_all(
                        reward_line_values["price_unit"],
                        currency=self.currency_id,
                    )
                    new_price = tax_res["total_excluded"]
                    new_price += sum(
                        tax_data["amount"]
                        for tax_data in tax_res["taxes"]
                        if tax_data["id"] in price_incl_taxes.ids
                    )
                    reward_line_values.update(
                        {
                            "price_unit": new_price,
                            "tax_id": [Command.set(mapped_taxes.ids)],
                        }
                    )
            return [reward_line_values]
        discount_factor = min(1, (max_discount / discountable)) if discountable else 1
        reward_dict = {}
        for tax, price in discountable_per_tax.items():
            if not price:
                continue
            mapped_taxes = self.fiscal_position_id.map_tax(tax)
            tax_desc = ""
            if any(t.name for t in mapped_taxes):
                tax_desc = _(
                    " - On product with the following taxes: %(taxes)s",
                    taxes=", ".join(mapped_taxes.mapped("name")),
                )
            # START HOOK
            reward_dict[tax] = self._reward_by_tax(
                tax,
                tax_desc,
                reward,
                reward.discount_line_product_id,
                price,
                discount_factor,
                coupon,
                reward_code,
                sequence,
                mapped_taxes,
            )
            # END HOOK
        # We only assign the point cost to one line to avoid counting the cost multiple times
        if reward_dict:
            reward_dict[next(iter(reward_dict))]["points_cost"] = point_cost
        # Returning .values() directly does not return a subscribable list
        return list(reward_dict.values())

    if not hasattr(SaleOrder, "_get_reward_values_discount_original"):
        SaleOrder._get_reward_values_discount_original = (
            SaleOrder._get_reward_values_discount
        )
    SaleOrder._get_reward_values_discount = _new_get_reward_values_discount
