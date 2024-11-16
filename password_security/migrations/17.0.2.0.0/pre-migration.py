# Copyright 2024 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(
        env,
        [
            (
                "res.company",
                "res_company",
                "password_expiration",
                openupgrade.get_legacy_name("password_expiration"),
            ),
            (
                "res.company",
                "res_company",
                "password_lower",
                openupgrade.get_legacy_name("password_lower"),
            ),
            (
                "res.company",
                "res_company",
                "password_upper",
                openupgrade.get_legacy_name("password_upper"),
            ),
            (
                "res.company",
                "res_company",
                "password_numeric",
                openupgrade.get_legacy_name("password_numeric"),
            ),
            (
                "res.company",
                "res_company",
                "password_special",
                openupgrade.get_legacy_name("password_special"),
            ),
            (
                "res.company",
                "res_company",
                "password_history",
                openupgrade.get_legacy_name("password_history"),
            ),
            (
                "res.company",
                "res_company",
                "password_minimum",
                openupgrade.get_legacy_name("password_minimum"),
            ),
        ],
    )
