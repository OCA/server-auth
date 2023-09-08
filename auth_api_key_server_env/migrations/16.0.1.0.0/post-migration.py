from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    keys = env["auth.api.key"].search(
        [("tech_name", "=", False), ("name", "!=", False)]
    )
    for key in keys:
        key.write({"tech_name": key._normalize_tech_name(key.name)})
