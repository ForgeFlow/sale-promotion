# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="loyalty_program_partner_rel",
        column1="loyalty_program_id",
        column2="partner_id",
        string="Customers linked to the program",
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    loyalty_program_ids = fields.Many2many(
        comodel_name="loyalty.program",
        relation="loyalty_program_partner_rel",
        column1="partner_id",
        column2="loyalty_program_id",
        string="Loyalty Programs",
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_claimable_rewards(self, forced_coupons=None):
        res = super()._get_claimable_rewards(forced_coupons)
        partner_loyalty_programs = self.partner_id.loyalty_program_ids
        if not partner_loyalty_programs:
            return defaultdict(lambda: self.env["loyalty.reward"])
        for coupon, rewards in list(res.items()):
            # Filter rewards that are linked to the partner's loyalty programs
            filtered_rewards = rewards.filtered(
                lambda reward: reward.program_id in partner_loyalty_programs
            )
            if filtered_rewards:
                res[coupon] = filtered_rewards
            else:
                del res[coupon]
        return res
