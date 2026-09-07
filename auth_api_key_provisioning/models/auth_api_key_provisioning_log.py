# Copyright 2026 Keboola
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AuthApiKeyProvisioningLog(models.Model):
    """Provenance + audit trail for keys minted by this module.

    ``res.users.apikeys`` is a raw ``_auto=False`` table with a fixed schema, so we
    cannot tag the key record itself with extra columns. Instead every minted key is
    recorded here, which gives us (a) a reliable handle to revoke by -- never by name
    matching -- and (b) an auditable history of who minted what, for whom, and when.

    The link to the key uses ``ondelete="set null"`` so the audit row survives the key
    being removed (by revocation, native expiry GC, or manual deletion).
    """

    _name = "auth.api.key.provisioning.log"
    _description = "Auth API Key Provisioning Log"
    _order = "create_date desc, id desc"
    _rec_name = "key_name"

    apikey_id = fields.Many2one(
        "res.users.apikeys",
        string="API Key",
        ondelete="set null",
        readonly=True,
        help="The minted key. Empty once the key has been revoked, expired or removed.",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Target User",
        required=True,
        readonly=True,
        ondelete="cascade",
        index=True,
        help="User the key was minted for; the key carries this user's "
        "own permissions.",
    )
    minted_by_id = fields.Many2one(
        "res.users",
        required=True,
        readonly=True,
        help="User (the provisioning/service account) that requested the mint.",
    )
    key_name = fields.Char(string="Label", readonly=True)
    scope = fields.Char(readonly=True, default="rpc")
    expiration = fields.Datetime(readonly=True)
    revoked_on = fields.Datetime(
        readonly=True,
        help="Set when this module actively revoked the key "
        "(manual revoke or automatic privilege-drift / offboarding revoke).",
    )
    is_live = fields.Boolean(
        string="Live",
        compute="_compute_is_live",
        help="True while the underlying key record still exists.",
    )

    @api.depends("apikey_id")
    def _compute_is_live(self):
        # res.users.apikeys is _auto=False (no FK on apikey_id), so a key removed
        # outside this module leaves a dangling id; check real existence.
        for log in self:
            log.is_live = bool(log.apikey_id and log.apikey_id.exists())
