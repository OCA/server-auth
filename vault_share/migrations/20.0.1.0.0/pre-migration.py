# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tools import SQL

# The access rights and record rules were merged into ir.access in 20.0, keeping
# the same external ids. Remove the external ids still pointing to the old models
# so that they can be loaded again as ir.access records.
OLD_MODELS = ("ir.model.access", "ir.rule")


def migrate(cr, version):
    cr.execute(
        SQL(
            "DELETE FROM ir_model_data WHERE module = %s AND model IN %s",
            "vault_share",
            OLD_MODELS,
        )
    )
