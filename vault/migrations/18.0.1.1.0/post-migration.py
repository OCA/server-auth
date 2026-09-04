# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    group = env.ref("vault.group_vault_user", raise_if_not_found=False)
    if not group:
        return

    # Grant the new "User" group to all existing internal users
    users = env["res.users"].search(
        [("share", "=", False), ("id", "not in", group.users.ids)]
    )
    if not users:
        return

    group.sudo().write({"users": [(4, user.id) for user in users]})
    _logger.info(
        "Added %d existing internal users to vault.group_vault_user", len(users)
    )
