# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Set the default strict sync parameter upon module installation."""
    param_key = "auth_user_role.strict_sync"

    # Only set it to 'True' if it doesn't already exist in the database
    if not env["ir.config_parameter"].sudo().get_param(param_key):
        env["ir.config_parameter"].sudo().set_param(param_key, "True")
