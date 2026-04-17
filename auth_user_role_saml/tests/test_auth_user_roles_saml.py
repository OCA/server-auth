# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import date, timedelta

from odoo.tests.common import TransactionCase

from odoo.addons.auth_saml.tests.fake_idp import DummyResponse


class TestAuthUserRolesSaml(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.test_role = cls.env["res.users.role"].create({"name": "Test Global Role"})
        cls.extra_manual_role = cls.env["res.users.role"].create(
            {"name": "Extra Manual Role"}
        )

        cls.provider = cls.env["auth.saml.provider"].create(
            {
                "name": "Test SAML Bridge Provider",
                "idp_metadata": "<EntityDescriptor></EntityDescriptor>",
                "sp_pem_public": base64.b64encode(b"fake_public_key"),
                "sp_pem_private": base64.b64encode(b"fake_private_key"),
                "matching_attribute": "mail",
                "sig_alg": "SIG_RSA_SHA1",
                "sync_roles_strictly": False,  # Defaults to False
            }
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
                "name": "Test SAML User",
                "login": "user2@example.com",
            }
        )
        cls.env["res.users.saml"].create(
            {
                "user_id": cls.user.id,
                "saml_provider_id": cls.provider.id,
                "saml_uid": "user2@example.com",
            }
        )

    def _simulate_saml_signin(self, identity_payload):
        """
        Simulates the exact two-step SAML login process to prevent false positives.
        """
        fake_response = DummyResponse(200, "fake_data")
        if identity_payload is not None:
            fake_response.set_identity(identity_payload)

        validation_extras = (
            self.provider._hook_validate_auth_response(
                fake_response, "user2@example.com"
            )
            or {}
        )

        validation = {"user_id": "user2@example.com"}
        validation.update(validation_extras)

        self.env["res.users"]._auth_saml_signin(
            self.provider.id, validation, "raw_base64_saml_string"
        )

    def test_01_hook_evaluation_equals(self):
        """Testing bridge intercepts signin and applies 'equals' mapping"""
        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": ["role2"]}
        )
        self.assertIn(self.test_role.id, self.user.role_line_ids.mapped("role_id").ids)

    def test_02_hook_evaluation_contains(self):
        self.mapping.write({"operator": "contains", "value": "admin"})
        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": ["super_admin_user"]}
        )
        self.assertIn(self.test_role.id, self.user.role_line_ids.mapped("role_id").ids)

    def test_03_missing_attribute_clears_roles(self):
        """With strict_sync, missing mapped attributes should clear previously
        granted roles."""
        self.provider.write({"sync_roles_strictly": True})
        self.user.write({"role_line_ids": [(0, 0, {"role_id": self.test_role.id})]})
        self._simulate_saml_signin({"mail": "user2@example.com"})
        self.assertNotIn(
            self.test_role.id, self.user.role_line_ids.mapped("role_id").ids
        )

    def test_04_string_vs_list_attribute(self):
        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": "role2"}
        )
        self.assertIn(self.test_role.id, self.user.role_line_ids.mapped("role_id").ids)

    def test_05_multiple_mappings(self):
        self.env["auth.user.role.mapping"].create(
            {
                "attribute": "department",
                "operator": "equals",
                "value": "IT",
                "role_id": self.extra_manual_role.id,
            }
        )
        self._simulate_saml_signin(
            {
                "mail": "user2@example.com",
                "eduPersonAffiliation": ["role2"],
                "department": ["IT"],
            }
        )
        roles_assigned = self.user.role_line_ids.mapped("role_id").ids
        self.assertIn(self.test_role.id, roles_assigned)
        self.assertIn(self.extra_manual_role.id, roles_assigned)

    def test_06_case_sensitivity(self):
        self.mapping.write({"operator": "equals", "value": "role2"})
        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": ["ROLE2"]}
        )
        self.assertNotIn(
            self.test_role.id, self.user.role_line_ids.mapped("role_id").ids
        )

    def test_07_repeated_login_idempotency(self):
        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": ["role2"]}
        )
        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": ["role2"]}
        )
        role_lines = self.user.role_line_ids.filtered(
            lambda r: r.role_id == self.test_role
        )
        self.assertEqual(len(role_lines), 1)

    def test_08_multiple_values_same_attribute(self):
        role3 = self.env["res.users.role"].create({"name": "Role 3"})
        self.env["auth.user.role.mapping"].create(
            {
                "attribute": "eduPersonAffiliation",
                "operator": "equals",
                "value": "role3",
                "role_id": role3.id,
            }
        )
        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": ["role2", "role3"]}
        )
        roles_assigned = self.user.role_line_ids.mapped("role_id").ids
        self.assertIn(self.test_role.id, roles_assigned)
        self.assertIn(role3.id, roles_assigned)

    def test_09_reactivate_expired_role(self):
        yesterday = date.today() - timedelta(days=1)
        self.user.write(
            {
                "role_line_ids": [
                    (0, 0, {"role_id": self.test_role.id, "date_to": yesterday})
                ]
            }
        )
        self.assertNotIn(
            self.test_role.id, self.user._get_enabled_roles().mapped("role_id").ids
        )

        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": ["role2"]}
        )

        role_line = self.user.role_line_ids.filtered(
            lambda r: r.role_id == self.test_role
        )
        self.assertEqual(len(role_line), 1)
        self.assertFalse(role_line.date_to)
        self.assertIn(
            self.test_role.id, self.user._get_enabled_roles().mapped("role_id").ids
        )

    def test_10_no_roles_in_validation_bypass(self):
        """Test the edge case where the IDP identity payload is explicitly None."""
        self.user.write({"role_line_ids": [(0, 0, {"role_id": self.test_role.id})]})

        validation = {"user_id": "user2@example.com", "saml_identity_payload": None}

        self.env["res.users"]._auth_saml_signin(
            self.provider.id, validation, "raw_base64_saml_string"
        )

        self.assertIn(self.test_role.id, self.user.role_line_ids.mapped("role_id").ids)

    def test_11_duplicate_role_mappings_deduplication(self):
        self.env["auth.user.role.mapping"].create(
            {
                "attribute": "department",
                "operator": "equals",
                "value": "IT",
                "role_id": self.test_role.id,
            }
        )
        self._simulate_saml_signin(
            {
                "mail": "user2@example.com",
                "eduPersonAffiliation": ["role2"],
                "department": ["IT"],
            }
        )

        role_lines = self.user.role_line_ids.filtered(
            lambda r: r.role_id == self.test_role
        )
        self.assertEqual(len(role_lines), 1)

    def test_12_empty_list_attribute_clears_roles(self):
        """If a mapped attribute returns an empty list and strict sync is on,
        the role should be cleared."""
        self.provider.write({"sync_roles_strictly": True})

        self.user.write({"role_line_ids": [(0, 0, {"role_id": self.test_role.id})]})
        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": []}
        )
        self.assertNotIn(
            self.test_role.id, self.user.role_line_ids.mapped("role_id").ids
        )

    def test_13_empty_identity_payload_clears_roles(self):
        """If a user has lost all roles in the IdP, the payload is {},
        and Odoo roles must be stripped."""
        self.provider.write({"sync_roles_strictly": True})
        self.user.write({"role_line_ids": [(0, 0, {"role_id": self.test_role.id})]})

        self._simulate_saml_signin({})

        self.assertNotIn(
            self.test_role.id, self.user.role_line_ids.mapped("role_id").ids
        )

    def test_14_strict_sync_removes_unmapped_roles(self):
        """Strict sync MUST remove manually assigned unmapped roles."""
        self.provider.write({"sync_roles_strictly": True})
        self.user.write(
            {"role_line_ids": [(0, 0, {"role_id": self.extra_manual_role.id})]}
        )

        self._simulate_saml_signin(
            {"mail": "user2@example.com", "eduPersonAffiliation": ["role2"]}
        )

        roles_assigned = self.user.role_line_ids.mapped("role_id").ids
        self.assertIn(self.test_role.id, roles_assigned)
        self.assertNotIn(self.extra_manual_role.id, roles_assigned)

    def test_15_default_strict_sync_from_config(self):
        """Test that a new SAML provider inherits the global strict_sync parameter."""

        # Set the global parameter to True
        self.env["ir.config_parameter"].set_param("auth_user_role.strict_sync", "True")

        # Create a new provider WITHOUT explicitly setting sync_roles_strictly
        provider_true = self.env["auth.saml.provider"].create(
            {
                "name": "Default True Test Provider",
                "idp_metadata": "<EntityDescriptor></EntityDescriptor>",
                "sp_pem_public": base64.b64encode(b"fake_public_key"),
                "sp_pem_private": base64.b64encode(b"fake_private_key"),
                "matching_attribute": "mail",
                "sig_alg": "SIG_RSA_SHA1",
            }
        )

        # It should default to True based on the global parameter
        self.assertTrue(provider_true.sync_roles_strictly)

        # Change the global parameter to False
        self.env["ir.config_parameter"].set_param("auth_user_role.strict_sync", "False")

        # Create another provider WITHOUT explicitly setting sync_roles_strictly
        provider_false = self.env["auth.saml.provider"].create(
            {
                "name": "Default False Test Provider",
                "idp_metadata": "<EntityDescriptor></EntityDescriptor>",
                "sp_pem_public": base64.b64encode(b"fake_public_key"),
                "sp_pem_private": base64.b64encode(b"fake_private_key"),
                "matching_attribute": "mail",
                "sig_alg": "SIG_RSA_SHA1",
            }
        )

        # It should now default to False based on the updated parameter
        self.assertFalse(provider_false.sync_roles_strictly)
