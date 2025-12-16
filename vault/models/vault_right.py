# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class VaultRight(models.Model):
    _name = "vault.right"
    _description = "Vault rights"
    _inherit = ["vault.abstract"]
    _order = "user_id"

    vault_id = fields.Many2one(
        "vault",
        "Vault",
        readonly=True,
        required=True,
        ondelete="cascade",
    )
    master_key = fields.Char(related="vault_id.master_key", readonly=True, store=False)
    user_id = fields.Many2one(
        "res.users",
        "User",
        domain=[("keys", "!=", False)],
        required=True,
    )
    public_key = fields.Char(compute="_compute_public_key", readonly=True, store=False)
    perm_create = fields.Boolean(
        "Create",
        default=lambda self: self._get_is_owner(),
        help="Allow to create in the vault",
    )
    perm_write = fields.Boolean(
        "Write",
        default=lambda self: self._get_is_owner(),
        help="Allow to write to the vault",
    )
    perm_share = fields.Boolean(
        "Share",
        default=lambda self: self._get_is_owner(),
        help="Allow to share a vault with new users",
    )
    perm_delete = fields.Boolean(
        "Delete",
        default=lambda self: self._get_is_owner(),
        help="Allow to delete a vault",
    )

    perm_user = fields.Many2one(related="vault_id.perm_user", store=False)
    allowed_read = fields.Boolean(related="vault_id.allowed_read", store=False)
    allowed_create = fields.Boolean(related="vault_id.allowed_create", store=False)
    allowed_write = fields.Boolean(related="vault_id.allowed_write", store=False)
    allowed_share = fields.Boolean(related="vault_id.allowed_share", store=False)
    allowed_delete = fields.Boolean(related="vault_id.allowed_delete", store=False)

    # Encrypted with the public key of the user
    key = fields.Char()

    _sql_constraints = (
        ("user_uniq", "UNIQUE(user_id, vault_id)", "The user must be unique"),
    )

    def _get_is_owner(self):
        return self.env.user == self.vault_id.user_id

    @api.depends("user_id")
    def _compute_public_key(self):
        for rec in self:
            rec.public_key = rec.user_id.active_key.public

    def log_access(self):
        for rec in self:
            rights = ", ".join(
                sorted(
                    ["read"]
                    + [
                        right
                        for right in ["create", "write", "share", "delete"]
                        if getattr(rec, f"perm_{right}", False)
                    ]
                )
            )

            rec.vault_id.log_info(
                f"Grant access to user {rec.user_id.display_name}: {rights}"
            )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if not res.allowed_share and not res.env.su:
            self.raise_access_error()

        res.log_access()
        return res

    def write(self, values):
        res = super().write(values)
        perms = ["perm_write", "perm_delete", "perm_share", "perm_create"]
        if any(x in values for x in perms):
            self.log_access()

        return res

    def unlink(self):
        for rec in self:
            rec.vault_id.log_info(f"Removed user {self.user_id.display_name}")
            rec.vault_id.reencrypt_required = True

        return super().unlink()
