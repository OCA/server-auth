# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tools import SQL

# Binary fields stored in a column (attachment=False) used to contain the base64
# encoded text. Since 20.0 the ORM stores the raw bytes, so decode the old values.
# Values which aren't plain base64 text are left untouched.
COLUMNS = [
    ("vault_file", "value"),
    ("vault_inbox", "secret_file"),
]


def migrate(cr, version):
    for table, column in COLUMNS:
        col = SQL.identifier(column)
        cr.execute(
            SQL(
                """
                UPDATE %(table)s
                SET %(col)s = decode(encode(%(col)s, 'escape'), 'base64')
                WHERE %(col)s IS NOT NULL
                    AND encode(%(col)s, 'escape') ~ %(pattern)s
                """,
                table=SQL.identifier(table),
                col=col,
                pattern=r"^[A-Za-z0-9+/=\s]+$",
            )
        )
