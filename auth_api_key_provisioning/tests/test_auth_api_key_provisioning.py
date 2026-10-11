# Copyright 2026 Keboola
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

# Auto-revocation intentionally logs at WARNING (a security-relevant event in
# production); mute it on the tests that deliberately trigger it so the OCA test
# runner does not flag the expected warnings as "errors in log".
_REVOKE_LOGGER = "odoo.addons.auth_api_key_provisioning.models.res_users"


class TestAuthApiKeyProvisioning(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResUsers = cls.env["res.users"]
        cls.Log = cls.env["auth.api.key.provisioning.log"]
        cls.ApiKeys = cls.env["res.users.apikeys"]

        cls.group_provisioning = cls.env.ref(
            "auth_api_key_provisioning.group_apikey_provisioning"
        )
        cls.group_mintable = cls.env.ref(
            "auth_api_key_provisioning.group_apikey_mintable_target"
        )
        cls.group_internal = cls.env.ref("base.group_user")
        cls.group_system = cls.env.ref("base.group_system")
        cls.group_portal = cls.env.ref("base.group_portal")

        # Caller / service account: allowed to mint, nothing more.
        cls.caller = cls.ResUsers.create(
            {
                "name": "Provisioning Service",
                "login": "prov-svc",
                "groups_id": [(6, 0, [cls.group_provisioning.id])],
            }
        )
        # A regular internal user explicitly marked as a mintable target.
        cls.target = cls.ResUsers.create(
            {
                "name": "Target User",
                "login": "target-user",
                "groups_id": [(6, 0, [cls.group_internal.id, cls.group_mintable.id])],
            }
        )
        # An internal user NOT in the mintable allowlist.
        cls.non_mintable = cls.ResUsers.create(
            {
                "name": "Non Mintable",
                "login": "non-mintable",
                "groups_id": [(6, 0, [cls.group_internal.id])],
            }
        )

    def _mint_model(self):
        """res.users model bound to the caller (the provisioning service account)."""
        return self.ResUsers.with_user(self.caller)

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------
    def test_mint_happy_path(self):
        target = self.target.with_user(self.caller)
        key = target.mint_apikey(name="ci", ttl_days=10)
        self.assertIsInstance(key, str)
        self.assertTrue(key)

        log = self.Log.search([("user_id", "=", self.target.id)])
        self.assertEqual(len(log), 1)
        self.assertEqual(log.minted_by_id, self.caller)
        self.assertEqual(log.scope, "rpc")
        self.assertTrue(log.apikey_id)
        self.assertTrue(log.is_live)
        self.assertFalse(log.revoked_on)
        # Key belongs to the target, scoped rpc, with an expiration ~10 days out.
        self.assertEqual(log.apikey_id.user_id, self.target)
        self.assertEqual(log.apikey_id.scope, "rpc")
        delta = log.apikey_id.expiration_date - fields.Datetime.now()
        self.assertLess(abs(delta - timedelta(days=10)), timedelta(minutes=5))

    def test_default_and_clamped_ttl(self):
        target = self.target.with_user(self.caller)
        # No ttl -> default 30.
        target.mint_apikey(name="default-ttl")
        log = self.Log.search(
            [("user_id", "=", self.target.id)], order="id desc", limit=1
        )
        delta = log.apikey_id.expiration_date - fields.Datetime.now()
        self.assertLess(abs(delta - timedelta(days=30)), timedelta(minutes=5))

        # Excessive ttl -> clamped to max (90).
        target.mint_apikey(name="huge-ttl", ttl_days=9999)
        log = self.Log.search(
            [("user_id", "=", self.target.id)], order="id desc", limit=1
        )
        delta = log.apikey_id.expiration_date - fields.Datetime.now()
        self.assertLess(abs(delta - timedelta(days=90)), timedelta(minutes=5))

    # ------------------------------------------------------------------
    # Authorization / refusals
    # ------------------------------------------------------------------
    def test_mint_requires_caller_group(self):
        # non_mintable is a plain internal user, not in the provisioning group.
        target = self.target.with_user(self.non_mintable)
        with self.assertRaises(AccessError):
            target.mint_apikey(name="nope")

    def test_mint_refuses_non_mintable_target(self):
        target = self.non_mintable.with_user(self.caller)
        with self.assertRaises(AccessError):
            target.mint_apikey(name="nope")

    def test_mint_refuses_elevated_target(self):
        self.target.write({"groups_id": [(4, self.group_system.id)]})
        target = self.target.with_user(self.caller)
        with self.assertRaises(AccessError):
            target.mint_apikey(name="nope")

    def test_mint_refuses_superuser(self):
        root = self.env.ref("base.user_root")
        # Put root in the mintable group to prove the SUPERUSER guard still fires.
        root.sudo().write({"groups_id": [(4, self.group_mintable.id)]})
        with self.assertRaises(AccessError):
            root.with_user(self.caller).mint_apikey(name="nope")

    def test_mint_refuses_portal_target(self):
        portal = self.ResUsers.create(
            {
                "name": "Portal User",
                "login": "portal-user",
                "groups_id": [(6, 0, [self.group_portal.id])],
            }
        )
        # Force into the mintable allowlist to prove the share guard still fires.
        portal.write({"groups_id": [(4, self.group_mintable.id)]})
        with self.assertRaises(UserError):
            portal.with_user(self.caller).mint_apikey(name="nope")

    def test_mint_refuses_archived_target(self):
        self.target.write({"active": False})
        # Re-read to avoid acting on a stale recordset.
        target = self.target.with_user(self.caller)
        with self.assertRaises(UserError):
            target.mint_apikey(name="nope")

    # ------------------------------------------------------------------
    # Revocation
    # ------------------------------------------------------------------
    def test_manual_revoke(self):
        target = self.target.with_user(self.caller)
        target.mint_apikey(name="to-revoke")
        log = self.Log.search([("user_id", "=", self.target.id)])
        self.assertTrue(log.apikey_id)

        count = target.revoke_provisioned_apikeys()
        self.assertEqual(count, 1)
        log.invalidate_recordset()
        self.assertFalse(log.apikey_id)
        self.assertTrue(log.revoked_on)

    def test_revoke_requires_caller_group(self):
        with self.assertRaises(AccessError):
            self.target.with_user(self.non_mintable).revoke_provisioned_apikeys()

    # ------------------------------------------------------------------
    # Privilege drift (the critical case)
    # ------------------------------------------------------------------
    @mute_logger(_REVOKE_LOGGER)
    def test_drift_user_side_promotion_revokes(self):
        target = self.target.with_user(self.caller)
        target.mint_apikey(name="drift-user")
        log = self.Log.search([("user_id", "=", self.target.id)])
        self.assertTrue(log.apikey_id)

        # Promote target into an elevated group via the user record (res.users.write).
        self.target.write({"groups_id": [(4, self.group_system.id)]})
        log.invalidate_recordset()
        self.assertFalse(
            log.apikey_id, "minted key must be revoked when target is promoted"
        )
        self.assertTrue(log.revoked_on)

    @mute_logger(_REVOKE_LOGGER)
    def test_drift_group_side_promotion_revokes(self):
        target = self.target.with_user(self.caller)
        target.mint_apikey(name="drift-group")
        log = self.Log.search([("user_id", "=", self.target.id)])
        self.assertTrue(log.apikey_id)

        # Promote via the group record (res.groups.write with users command).
        self.group_system.write({"users": [(4, self.target.id)]})
        log.invalidate_recordset()
        self.assertFalse(
            log.apikey_id,
            "minted key must be revoked when target is added to elevated group "
            "from the group side",
        )

    @mute_logger(_REVOKE_LOGGER)
    def test_drift_implied_group_promotion_revokes(self):
        # Target holds an innocuous intermediate group...
        inter = self.env["res.groups"].create({"name": "Intermediate"})
        self.target.write({"groups_id": [(4, inter.id)]})
        target = self.target.with_user(self.caller)
        target.mint_apikey(name="drift-implied")
        log = self.Log.search([("user_id", "=", self.target.id)])
        self.assertTrue(log.apikey_id)

        # ...which is then made to imply an elevated group (no res.users.write, no
        # change to res.groups.users -- only implied_ids).
        inter.write({"implied_ids": [(4, self.group_system.id)]})
        log.invalidate_recordset()
        self.assertFalse(
            log.apikey_id,
            "minted key must be revoked when the target is elevated via implied_ids",
        )

    @mute_logger(_REVOKE_LOGGER)
    def test_drift_archive_revokes(self):
        target = self.target.with_user(self.caller)
        target.mint_apikey(name="drift-archive")
        log = self.Log.search([("user_id", "=", self.target.id)])
        self.assertTrue(log.apikey_id)

        self.target.write({"active": False})
        log.invalidate_recordset()
        self.assertFalse(log.apikey_id)

    @mute_logger(_REVOKE_LOGGER)
    def test_cron_backstop_revokes_drift(self):
        target = self.target.with_user(self.caller)
        target.mint_apikey(name="drift-cron")
        log = self.Log.search([("user_id", "=", self.target.id)])
        self.assertTrue(log.apikey_id)

        # Simulate drift the ORM write hooks did not see: drop the target from the
        # mintable allowlist via the relation table directly. has_group resolves
        # membership through an ormcache (_get_group_ids) that raw SQL does not
        # invalidate, so clear it to mimic a fresh cron process, then run the cron.
        self.env.cr.execute(
            "DELETE FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
            (self.target.id, self.group_mintable.id),
        )
        self.env.registry.clear_cache()
        self.env.invalidate_all()
        self.ResUsers._cron_revoke_drifted_apikeys()
        log.invalidate_recordset()
        self.assertFalse(log.apikey_id, "cron must revoke keys for a now-unsafe target")
