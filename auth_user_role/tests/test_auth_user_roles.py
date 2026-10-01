# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestAuthUserRoles(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].set_param("auth_user_role.strict_sync", "False")
        cls.test_role = cls.env["res.users.role"].create({"name": "Test Global Role"})
        cls.extra_manual_role = cls.env["res.users.role"].create(
            {"name": "Extra Manual Role"}
        )

        cls.mapping = cls.env["auth.user.role.mapping"].create(
            {
                "attribute": "eduPersonAffiliation",
                "operator": "equals",
                "value": "role2",
                "role_id": cls.test_role.id,
            }
        )

        cls.user = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "user2@example.com",
            }
        )

    def test_01_hook_evaluation_equals(self):
        payload = {"mail": "user2@example.com", "eduPersonAffiliation": ["role2"]}
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=False)
        self.assertIn(self.test_role, self.user.role_line_ids.mapped("role_id"))

    def test_02_hook_evaluation_contains(self):
        self.mapping.write({"operator": "contains", "value": "admin"})
        payload = {
            "mail": "user2@example.com",
            "eduPersonAffiliation": ["super_admin_user"],
        }
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=False)
        self.assertIn(self.test_role, self.user.role_line_ids.mapped("role_id"))

    def test_03_signin_strict_sync_mode_removes_manual(self):
        self.user.write(
            {"role_line_ids": [(0, 0, {"role_id": self.extra_manual_role.id})]}
        )
        payload = {"mail": "user2@example.com", "eduPersonAffiliation": ["role2"]}
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=True)
        assigned_roles = self.user.role_line_ids.mapped("role_id")

        self.assertNotIn(self.extra_manual_role, assigned_roles)
        self.assertIn(self.test_role, assigned_roles)

    def test_04_missing_attribute(self):
        payload = {"mail": "user2@example.com"}
        roles_added = self.user.evaluate_and_apply_auth_roles(
            payload, strict_sync=False
        )
        self.assertNotIn(self.test_role.id, roles_added)

    def test_05_string_vs_list_attribute(self):
        payload = {"mail": "user2@example.com", "eduPersonAffiliation": "role2"}
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=False)
        self.assertIn(self.test_role, self.user.role_line_ids.mapped("role_id"))

    def test_06_multiple_mappings(self):
        self.env["auth.user.role.mapping"].create(
            {
                "attribute": "department",
                "operator": "equals",
                "value": "IT",
                "role_id": self.extra_manual_role.id,
            }
        )
        payload = {
            "mail": "user2@example.com",
            "eduPersonAffiliation": ["role2"],
            "department": ["IT"],
        }
        roles_added = self.user.evaluate_and_apply_auth_roles(
            payload, strict_sync=False
        )

        self.assertIn(self.test_role.id, roles_added)
        self.assertIn(self.extra_manual_role.id, roles_added)

    def test_07_strict_sync_no_matches_removes_manual(self):
        self.user.write(
            {"role_line_ids": [(0, 0, {"role_id": self.extra_manual_role.id})]}
        )
        payload = {"mail": "user2@example.com"}
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=True)

        self.assertEqual(len(self.user.role_line_ids), 0)
        self.assertNotIn(
            self.extra_manual_role, self.user.role_line_ids.mapped("role_id")
        )

    def test_08_case_sensitivity(self):
        self.mapping.write({"operator": "equals", "value": "role2"})
        payload = {"mail": "user2@example.com", "eduPersonAffiliation": ["ROLE2"]}
        roles_added = self.user.evaluate_and_apply_auth_roles(
            payload, strict_sync=False
        )
        self.assertNotIn(self.test_role.id, roles_added)

    def test_09_repeated_login_idempotency(self):
        """Test that mapping application multiple times does not duplicate roles
        or crash."""
        payload = {"eduPersonAffiliation": ["role2"]}
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=False)
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=False)
        role_lines = self.user.role_line_ids.filtered(
            lambda r: r.role_id == self.test_role
        )
        self.assertEqual(len(role_lines), 1)

    def test_10_repeated_login_strict_sync(self):
        """Test repeated evaluation when strict_sync is True."""
        payload = {"eduPersonAffiliation": ["role2"]}
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=True)
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=True)
        role_lines = self.user.role_line_ids.filtered(
            lambda r: r.role_id == self.test_role
        )
        self.assertEqual(len(role_lines), 1)

    def test_11_multiple_values_same_attribute(self):
        """Test when the payload returns a list of multiple values for
        the same attribute."""
        role3 = self.env["res.users.role"].create({"name": "Role 3"})
        self.env["auth.user.role.mapping"].create(
            {
                "attribute": "eduPersonAffiliation",
                "operator": "equals",
                "value": "role3",
                "role_id": role3.id,
            }
        )
        payload = {
            "mail": "user2@example.com",
            "eduPersonAffiliation": ["role2", "role3"],
        }
        roles_added = self.user.evaluate_and_apply_auth_roles(
            payload, strict_sync=False
        )

        self.assertIn(self.test_role.id, roles_added)
        self.assertIn(role3.id, roles_added)

    def test_12_reactivate_expired_role(self):
        """Test that an expired role is reactivated instead of creating
        a duplicate constraint error."""
        yesterday = date.today() - timedelta(days=1)
        two_days_ago = date.today() - timedelta(days=2)

        self.user.write(
            {
                "role_line_ids": [
                    (
                        0,
                        0,
                        {
                            "role_id": self.test_role.id,
                            "date_from": two_days_ago,
                            "date_to": yesterday,
                        },
                    )
                ]
            }
        )
        self.assertNotIn(
            self.test_role.id, self.user._get_enabled_roles().mapped("role_id").ids
        )

        payload = {"eduPersonAffiliation": ["role2"]}
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=False)

        role_line = self.user.role_line_ids.filtered(
            lambda r: r.role_id == self.test_role
        )
        self.assertEqual(len(role_line), 1)
        self.assertFalse(role_line.date_to)
        self.assertEqual(role_line.date_from, two_days_ago)
        self.assertIn(
            self.test_role.id, self.user._get_enabled_roles().mapped("role_id").ids
        )

    def test_13_strict_sync_removes_native_groups(self):
        """Test that strict sync removes manually assigned native Odoo groups."""
        native_group = self.env.ref("base.group_user")
        self.user.write({"groups_id": [(4, native_group.id)]})
        self.assertIn(native_group, self.user.groups_id)
        self.assertNotIn(native_group, self.test_role.implied_ids)

        payload = {"eduPersonAffiliation": ["role2"]}
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=True)

        # The unrelated manual native group is stripped by set_groups_from_roles
        self.assertNotIn(native_group, self.user.groups_id)
        # The role-managed group should be present
        self.assertIn(self.test_role.group_id, self.user.groups_id)

    def test_14_duplicate_role_mappings_deduplication(self):
        """Test when multiple different mappings resolve to the EXACT SAME role."""
        self.env["auth.user.role.mapping"].create(
            {
                "attribute": "department",
                "operator": "equals",
                "value": "IT",
                "role_id": self.test_role.id,
            }
        )
        payload = {
            "mail": "user2@example.com",
            "eduPersonAffiliation": ["role2"],
            "department": ["IT"],
        }

        roles_added = self.user.evaluate_and_apply_auth_roles(
            payload, strict_sync=False
        )
        self.assertEqual(roles_added.count(self.test_role.id), 1)

        role_lines = self.user.role_line_ids.filtered(
            lambda r: r.role_id == self.test_role
        )
        self.assertEqual(len(role_lines), 1)

    def test_15_empty_list_attribute(self):
        """Test when the payload returns an empty list for a mapped attribute."""
        payload = {"mail": "user2@example.com", "eduPersonAffiliation": []}
        roles_added = self.user.evaluate_and_apply_auth_roles(
            payload, strict_sync=False
        )
        self.assertNotIn(self.test_role.id, roles_added)

    def test_16_empty_identity_payload(self):
        """Test when the payload is entirely empty."""
        payload = {}
        roles_added = self.user.evaluate_and_apply_auth_roles(
            payload, strict_sync=False
        )
        self.assertNotIn(self.test_role.id, roles_added)

    def test_17_strict_sync_zero_roles_removes_all_groups(self):
        """If a user drops to zero roles under strict sync, remove all groups."""
        native_group = self.env.ref("base.group_user")
        self.user.write({"groups_id": [(4, native_group.id)]})

        # Ensure they actually have it
        self.assertIn(native_group, self.user.groups_id)

        # Send a payload that matches no roles with strict_sync=True
        payload = {"mail": "user2@example.com"}  # no mapped attributes
        self.user.evaluate_and_apply_auth_roles(payload, strict_sync=True)

        # Assert roles dropped to 0
        self.assertEqual(len(self.user.role_line_ids), 0)

        # Assert ALL groups were wiped (including the manual native group)
        self.assertEqual(len(self.user.groups_id), 0)
