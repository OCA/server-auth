# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestResUsersWriteTotpSecret(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.portal_user = new_test_user(
            cls.env, login="portal-write-totp", groups="base.group_portal"
        )
        cls.internal_user = new_test_user(
            cls.env, login="internal-write-totp", groups="base.group_user"
        )
        cls.vault = cls.env["vault"].create({"name": "Write totp test vault"})

        cls.env["ir.config_parameter"].sudo().set_param(
            "vault_portal.mfa_policy", "read"
        )

    def _grant_right(self, user):
        user.sudo().totp_secret = "AAAAAAAAAAAAAAAA"
        return self.env["vault.right"].create(
            {"vault_id": self.vault.id, "user_id": user.id}
        )

    def test_enabling_totp_does_not_trigger_policy(self):
        right = self._grant_right(self.portal_user)
        self.portal_user.sudo().totp_secret = "BBBBBBBBBBBBBBBB"
        self.assertTrue(right.exists())

    def test_unrelated_write_does_not_trigger_policy(self):
        right = self._grant_right(self.portal_user)
        self.portal_user.sudo().name = "New name"
        self.assertTrue(right.exists())

    def test_disabling_totp_for_internal_user_has_no_effect(self):
        self.internal_user.sudo().totp_secret = "AAAAAAAAAAAAAAAA"
        self.internal_user.sudo().totp_secret = False
