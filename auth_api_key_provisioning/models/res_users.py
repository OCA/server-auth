# Copyright 2026 Keboola
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from datetime import timedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

# Group whose members are allowed to mint/revoke keys for other users (the caller).
# Deliberately NOT base.group_system: a dedicated least-privilege capability.
PROVISIONING_GROUP = "auth_api_key_provisioning.group_apikey_provisioning"

# Allowlist group: a key may only be minted for a user placed in this group. An
# allowlist (not blocklist) because Odoo's modular ecosystem makes any fixed blocklist
# of "dangerous" groups incomplete -- custom modules add their own privileged groups.
MINTABLE_TARGET_GROUP = "auth_api_key_provisioning.group_apikey_mintable_target"

# Defence-in-depth: even if mis-added to the allowlist, these targets are refused.
ELEVATED_GROUPS = ("base.group_system", "base.group_erp_manager")

# ir.config_parameter keys (operator-tunable) and the absolute code ceiling.
PARAM_DEFAULT_TTL = "auth_api_key_provisioning.default_ttl_days"
PARAM_MAX_TTL = "auth_api_key_provisioning.max_ttl_days"
HARD_MAX_TTL_DAYS = 365  # absolute upper bound regardless of misconfiguration

# Mirrors odoo.addons.base.models.res_users.INDEX_SIZE (hex digits of the key used as a
# public lookup index). Used to locate the freshly minted key record precisely.
APIKEY_INDEX_SIZE = 8


def _safe_int(value, fallback):
    """int(value) but never raises -- returns ``fallback`` on bad/empty input."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


class ResUsers(models.Model):
    _inherit = "res.users"

    # ------------------------------------------------------------------
    # Public RPC API
    # ------------------------------------------------------------------
    def mint_apikey(self, name=None, ttl_days=None):
        """Mint a fresh ``rpc``-scoped API key for ``self`` and return it once.

        Intended to be called over RPC by a provisioning/service account (a member of
        the *API Key Provisioning* group), e.g. ``execute_kw('res.users',
        'mint_apikey', [[target_uid]], {'name': ..., 'ttl_days': ...})``. The minted key
        authenticates as ``self`` with that user's own record rules and correct
        ``create_uid`` -- it does NOT carry the caller's privileges.

        :param str name: optional human label for the key.
        :param int ttl_days: optional lifetime in days; clamped to the configured max.
        :returns str: the freshly generated API key (shown only once).
        :raises AccessError: caller not in the provisioning group; target is the
            superuser / elevated user; or target not in the mintable allowlist.
        :raises UserError: target is archived or not an internal user.
        """
        self._apikey_provisioning_assert_caller()
        self.ensure_one()
        # The caller is authorized by the provisioning-group gate above; inspect the
        # target under sudo. The provisioning account is deliberately low-privilege and
        # need not have read access to res.users, and Odoo 18 only allows has_group()
        # for the current user unless in a sudo (superuser) environment.
        target = self.sudo()

        # Anti-escalation refusal first (strongest, and independent of active/share):
        # never mint for the superuser or an admin/elevated user, even if they were
        # mistakenly added to the mintable allowlist.
        if target.id == SUPERUSER_ID or any(
            target.has_group(g) for g in ELEVATED_GROUPS
        ):
            raise AccessError(
                _("Refusing to mint an API key for an elevated/admin user (%s).")
                % target.login
            )
        if not target.active:
            raise UserError(
                _("Cannot mint an API key for an archived user (%s).") % target.login
            )
        if target.share:
            raise UserError(
                _("Cannot mint an API key for a non-internal user (%s).") % target.login
            )
        if not target.has_group(MINTABLE_TARGET_GROUP):
            raise AccessError(
                _(
                    "User %s is not in the 'API Key Mintable Target' group; "
                    "refusing to mint a key for them."
                )
                % target.login
            )

        days = target._apikey_provisioning_clamped_ttl(ttl_days)
        expiration = fields.Datetime.now() + timedelta(days=days)
        label = name or _("Provisioned key")

        # Generate as the target user (with_user) so the key belongs to them; sudo() so
        # the low-level _generate may set an explicit expiration regardless of the
        # target's own api_key_duration policy. with_user keeps uid == target, so the
        # key row's user_id is the target (not the superuser).
        apikeys_sudo = self.env["res.users.apikeys"].with_user(target).sudo()
        # Watermark the table id before generating so we can identify *exactly* the row
        # _generate inserts (it returns only the plaintext, not the record).
        self.env.cr.execute("SELECT COALESCE(MAX(id), 0) FROM res_users_apikeys")
        max_id_before = self.env.cr.fetchone()[0]
        api_key = apikeys_sudo._generate("rpc", label, expiration)

        minted = target._apikey_provisioning_find_minted_key(api_key, max_id_before)
        if not minted:
            # We could not positively identify the row we just created, so we cannot
            # track (and therefore later revoke) it. Refuse rather than leave an
            # untracked live key: raising rolls back the _generate INSERT in this
            # transaction. Should be unreachable in practice.
            raise UserError(
                _("Could not register the minted API key for tracking; aborted.")
            )
        self.env["auth.api.key.provisioning.log"].sudo().create(
            {
                "apikey_id": minted.id,
                "user_id": target.id,
                "minted_by_id": self.env.uid,
                "key_name": label,
                "scope": "rpc",
                "expiration": expiration,
            }
        )
        _logger.info(
            "Provisioned rpc API key for user_id=%s by uid=%s (label=%s, ttl_days=%s)",
            target.id,
            self.env.uid,
            label,
            days,
        )
        return api_key

    def revoke_provisioned_apikeys(self):
        """Revoke every key this module minted for ``self``; returns the count."""
        self._apikey_provisioning_assert_caller()
        return self._apikey_provisioning_revoke()

    # ------------------------------------------------------------------
    # Privilege-drift / offboarding protection
    # ------------------------------------------------------------------
    def write(self, vals):
        res = super().write(vals)
        # An API key carries no permission snapshot: it authenticates as the user with
        # their *current* groups. If a user with provisioned keys is promoted into an
        # elevated group or archived after minting, those keys would silently inherit
        # the new power -- so revoke them immediately. The group-side path (editing
        # res.groups.users) is covered in res_groups.write and, as a backstop, by cron.
        if {"groups_id", "active", "share"} & set(vals):
            self._apikey_provisioning_revoke_if_unsafe()
        return res

    def _apikey_provisioning_revoke_if_unsafe(self):
        """Revoke provisioned keys for users in ``self`` no longer safe as targets.

        Work is bounded to users that actually hold a live provisioned key, so this
        stays cheap even when called for every member of a large group.
        """
        if not self:
            return
        log_model = self.env["auth.api.key.provisioning.log"].sudo()
        users_with_keys = log_model.search(
            [("user_id", "in", self.ids), ("apikey_id", "!=", False)]
        ).mapped("user_id")
        # sudo: this may run for users other than the current one (group writes, cron),
        # and Odoo 18 only allows has_group() for the current user outside sudo.
        for user in users_with_keys.sudo():
            unsafe = (
                not user.active
                or user.id == SUPERUSER_ID
                or user.share
                or any(user.has_group(g) for g in ELEVATED_GROUPS)
                or not user.has_group(MINTABLE_TARGET_GROUP)
            )
            if unsafe:
                count = user._apikey_provisioning_revoke()
                if count:
                    _logger.warning(
                        "Auto-revoked %s provisioned API key(s) for user_id=%s "
                        "(privilege drift / offboarding).",
                        count,
                        user.id,
                    )

    @api.model
    def _apikey_provisioning_sweep_all(self):
        """Re-check every user that currently holds a live provisioned key.

        Used as the daily cron and as the safe catch-all for group changes whose exact
        set of affected users is awkward to compute (e.g. transitive ``implied_ids``).
        Cheap: the live-key holder set is small in practice.
        """
        logs = (
            self.env["auth.api.key.provisioning.log"]
            .sudo()
            .search([("apikey_id", "!=", False)])
        )
        users = logs.mapped("user_id")
        if users:
            users._apikey_provisioning_revoke_if_unsafe()

    @api.model
    def _cron_revoke_drifted_apikeys(self):
        """Backstop sweep: revoke provisioned keys for any now-unsafe target.

        Catches drift introduced by paths that bypass the write() hooks (e.g. raw
        SQL, or group changes applied in ways the ORM hooks miss).
        """
        self._apikey_provisioning_sweep_all()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _apikey_provisioning_assert_caller(self):
        if not self.env.user.has_group(PROVISIONING_GROUP):
            raise AccessError(
                _(
                    "Only members of the 'API Key Provisioning' group may mint or "
                    "revoke API keys on behalf of other users."
                )
            )

    def _apikey_provisioning_clamped_ttl(self, ttl_days):
        icp = self.env["ir.config_parameter"].sudo()
        # A malformed system parameter must not be able to block minting: fall back to
        # the documented defaults instead of raising.
        default_ttl = _safe_int(icp.get_param(PARAM_DEFAULT_TTL), 30)
        max_ttl = _safe_int(icp.get_param(PARAM_MAX_TTL), 90)
        max_ttl = max(1, min(max_ttl, HARD_MAX_TTL_DAYS))
        days = _safe_int(ttl_days, default_ttl) if ttl_days else default_ttl
        return max(1, min(days, max_ttl))

    def _apikey_provisioning_find_minted_key(self, plaintext_key, max_id_before):
        """Locate the apikey record just created for ``self`` by ``_generate``.

        ``_generate`` performs a raw SQL INSERT and returns only the plaintext key, not
        the record. We identify the new row deterministically: it is the only row with
        ``id`` greater than the pre-insert watermark for this user and the rpc scope.
        The public ``index`` prefix (first ``APIKEY_INDEX_SIZE`` hex chars) is matched
        too as a defensive sanity check. Returns an empty recordset if not found.
        """
        self.ensure_one()
        index = plaintext_key[:APIKEY_INDEX_SIZE]
        self.env.cr.execute(
            """
            SELECT id FROM res_users_apikeys
            WHERE id > %s AND user_id = %s AND scope = 'rpc' AND index = %s
            ORDER BY id DESC LIMIT 1
            """,
            (max_id_before, self.id, index),
        )
        row = self.env.cr.fetchone()
        if not row:
            return self.env["res.users.apikeys"]
        return self.env["res.users.apikeys"].sudo().browse(row[0])

    def _apikey_provisioning_revoke(self):
        """Unlink the live keys recorded for ``self`` and stamp their audit rows."""
        log_model = self.env["auth.api.key.provisioning.log"].sudo()
        logs = log_model.search(
            [("user_id", "in", self.ids), ("apikey_id", "!=", False)]
        )
        if not logs:
            return 0
        # res.users.apikeys is an _auto=False table, so no FK is created for apikey_id
        # and ondelete="set null" never fires -- we must clear the link explicitly.
        # .exists() guards against rows whose key was already removed natively
        # (e.g. Odoo's expired-key autovacuum), which leave a dangling id behind.
        keys = logs.mapped("apikey_id").exists()
        count = len(keys)
        keys.sudo().unlink()
        logs.write({"apikey_id": False, "revoked_on": fields.Datetime.now()})
        return count
