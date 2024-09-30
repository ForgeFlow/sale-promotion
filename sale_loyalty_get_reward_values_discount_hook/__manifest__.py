# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Sale Loyalty Hooks",
    "summary": "Adds Hook to Sale Loalty get_reward_vakues_discount method.",
    "version": "16.0.1.0.0",
    "category": "Promotions",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": ["sale_loyalty"],
    "post_load": "post_load_hook",
}
