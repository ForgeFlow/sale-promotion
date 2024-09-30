# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class LoyaltyRewardTaxProduct(models.Model):
    _name = "loyalty.reward.tax.product"
    _description = "Loyalty Products by tax"

    name = fields.Char(required=True)
    tax_id = fields.Many2one("account.tax", required=True)
    product_id = fields.Many2one("product.product", required=True)
