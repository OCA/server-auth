# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env["auth.oauth.provider"]._preserve_not_env_managed_data(
        ["auth_endpoint", "token_endpoint", "jwks_uri"]
    )
