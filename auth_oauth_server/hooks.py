# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


def post_init_hook(env):
    """Pin the issuer to the current base URL.

    The issuer is a parameter of its own because ``web.base.url`` is rewritten
    on every administrator login unless frozen, and every change of issuer
    invalidates the access tokens issued so far.

    Dynamic client registration and client metadata documents stay off until
    an administrator enables them: otherwise anyone could register an
    application under any name and have users approve it.
    """
    params = env["ir.config_parameter"]
    if not params.get_param("auth_oauth_server.issuer"):
        base_url = params.get_param("web.base.url") or ""
        params.set_param("auth_oauth_server.issuer", base_url.rstrip("/"))
