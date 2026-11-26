# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Pin the issuer to the current base URL and enable client registration.

    The issuer is a parameter of its own because ``web.base.url`` is rewritten
    on every administrator login unless frozen, and every change of issuer
    invalidates the access tokens issued so far.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    params = env["ir.config_parameter"]
    if not params.get_param("auth_oauth_server.issuer"):
        base_url = params.get_param("web.base.url") or ""
        params.set_param("auth_oauth_server.issuer", base_url.rstrip("/"))
    for key in ("auth_oauth_server.cimd_enabled", "auth_oauth_server.dcr_enabled"):
        if not params.get_param(key):
            params.set_param(key, "True")
