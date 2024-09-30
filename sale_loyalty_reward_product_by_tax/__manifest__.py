# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Loyalty rewards products by tax",
    "summary": "Allows to set up reward products by tax",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["AaronHForgeFlow"],
    "license": "LGPL-3",
    "depends": [
        "sale_loyalty_get_reward_values_discount_hook",
        "sale_loyalty",
        "account_avatax_sale_oca",
    ],
    "data": ["security/ir.model.access.csv", "views/loyalty_reward_view.xml"],
}
