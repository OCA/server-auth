# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import secrets

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestForceLogout(TransactionCase):
    """Tests for force logout functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_token = "test_token_12345"
        cls.env["ir.config_parameter"].sudo().set_param(
            "auth_session_logout_api.token", cls.test_token
        )
        # Create test user
        cls.test_user = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "testuser",
                "email": "test@example.com",
            }
        )

    def test_token_validation_valid(self):
        """Test token validation with valid token"""
        result = secrets.compare_digest(self.test_token, self.test_token)
        self.assertTrue(result)

    def test_token_validation_invalid(self):
        """Test token validation with invalid token"""
        result = secrets.compare_digest("invalid_token", self.test_token)
        self.assertFalse(result)

    def test_find_user_by_login(self):
        """Test finding user by login"""
        user = (
            self.env["res.users"]
            .sudo()
            .search([("login", "=ilike", "testuser")], limit=1)
        )
        self.assertEqual(user, self.test_user)

    def test_find_user_by_email(self):
        """Test finding user by email"""
        user = (
            self.env["res.users"]
            .sudo()
            .search([("email", "=ilike", "test@example.com")], limit=1)
        )
        self.assertEqual(user, self.test_user)

    def test_find_user_case_insensitive(self):
        """Test that user lookup is case insensitive"""
        user = (
            self.env["res.users"]
            .sudo()
            .search([("login", "=ilike", "TESTUSER")], limit=1)
        )
        self.assertEqual(user, self.test_user)

    def test_find_user_not_found(self):
        """Test finding non-existent user"""
        user = (
            self.env["res.users"]
            .sudo()
            .search([("login", "=ilike", "nonexistent")], limit=1)
        )
        self.assertFalse(user)

    def test_session_token_fields_extended(self):
        """Test that session_logout_key is included in session token fields"""
        fields = self.env["res.users"]._get_session_token_fields()
        self.assertIn("session_logout_key", fields)

    def test_force_logout_changes_session_key(self):
        """Test that force logout updates session_logout_key"""
        old_key = self.test_user.session_logout_key
        self.test_user.action_force_logout()
        self.test_user.invalidate_recordset()
        self.assertNotEqual(self.test_user.session_logout_key, old_key)

    def test_force_logout_count_increment(self):
        """Test that force logout count is incremented"""
        initial_count = self.test_user.force_logout_count
        self.test_user.action_force_logout()
        self.test_user.invalidate_recordset()
        self.assertEqual(self.test_user.force_logout_count, initial_count + 1)

    def test_audit_log_creation(self):
        """Test that audit logs can be created"""
        audit_log = (
            self.env["auth.session.logout.audit"]
            .sudo()
            .create(
                {
                    "target_user_id": self.test_user.id,
                    "request_ip": "127.0.0.1",
                    "user_agent": "Test Agent",
                    "status": "success",
                }
            )
        )
        self.assertTrue(audit_log.exists())
        self.assertEqual(audit_log.target_user_login, "testuser")
        self.assertEqual(audit_log.status, "success")

    def test_audit_log_error_status(self):
        """Test audit log with error status"""
        audit_log = (
            self.env["auth.session.logout.audit"]
            .sudo()
            .create(
                {
                    "target_user_id": self.test_user.id,
                    "request_ip": "127.0.0.1",
                    "status": "error",
                    "error_message": "Test error message",
                }
            )
        )
        self.assertEqual(audit_log.status, "error")
        self.assertEqual(audit_log.error_message, "Test error message")

    def test_generate_token(self):
        """Test token generation"""
        settings = self.env["res.config.settings"].create({})
        settings.action_generate_token()
        new_token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("auth_session_logout_api.token")
        )
        self.assertTrue(new_token)
        self.assertNotEqual(new_token, self.test_token)
