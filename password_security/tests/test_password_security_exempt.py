# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestPasswordSecurityExempt(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env["res.partner"]
        cls.user_model = cls.env["res.users"]
        cls.password = "asdQWE123$%^"
        # time-based checks (expiration and the minimum delay between resets)
        exp_group = "password_security.group_password_security_exempt_expiration"
        cls.group_exempt_expiration = cls.env.ref(exp_group)
        # value-based checks (complexity and history)
        rule_group = "password_security.group_password_security_exempt_rules"
        cls.group_exempt_rules = cls.env.ref(rule_group)

    def _new_user(self, login):
        partner = self.partner_model.create(
            {
                "name": login,
                "email": login,
            }
        )
        return self.user_model.create(
            {
                "name": login,
                "login": login,
                "password": self.password,
                "partner_id": partner.id,
            }
        )

    def test_exempt_expiration_password_never_expires(self):
        # Password is expired unless user belongs to exempt group
        user = self._new_user("exempt-exp@example.com")
        user.write({"password_write_date": "1970-01-01 00:00:00"})
        user.invalidate_recordset()
        self.assertTrue(user._password_has_expired())
        user.groups_id |= self.group_exempt_expiration
        self.assertFalse(user._password_has_expired())

    def test_exempt_expiration_allows_reset_within_threshold(self):
        # Password cannot be reset unless user belongs to exempt group
        user = self._new_user("exempt-reset@example.com")
        # Freshly created -> still inside the minimum-hours window
        with self.assertRaises(UserError):
            user._validate_pass_reset()
        user.groups_id |= self.group_exempt_expiration
        self.assertTrue(user._validate_pass_reset())

    def test_exempt_rules_allows_weak_password(self):
        # Weak password cannot be set unless user belongs to exempt group
        user = self._new_user("exempt-weak@example.com")
        with self.assertRaises(UserError):
            user._check_password("password")
        user.groups_id |= self.group_exempt_rules
        self.assertTrue(user._check_password("password"))

    def test_exempt_rules_allows_password_reuse(self):
        # Reused password cannot be set unless user belongs to exempt group
        user = self._new_user("exempt-reuse@example.com")
        # Reusing the current password fails the history check
        with self.assertRaises(UserError):
            user.write({"password": self.password})
        user.groups_id |= self.group_exempt_rules
        user.write({"password": self.password})
        self.assertTrue(user._check_password(self.password))

    def test_expiration_exemption_does_not_relax_rules(self):
        user = self._new_user("only-exp@example.com")
        user.groups_id |= self.group_exempt_expiration
        with self.assertRaises(UserError):
            user._check_password("password")

    def test_rules_exemption_does_not_relax_expiration(self):
        user = self._new_user("only-rules@example.com")
        user.groups_id |= self.group_exempt_rules
        user.write({"password_write_date": "1970-01-01 00:00:00"})
        user.invalidate_recordset()
        self.assertTrue(user._password_has_expired())
