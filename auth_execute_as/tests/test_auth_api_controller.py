# Copyright 2026 Kencove (https://www.kencove.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import AccessError

from odoo.addons.auth_execute_as.controllers.main import AuthExecuteAsController

from .common import AuthExecuteAsTestCommon


class TestAuthExecuteAsController(AuthExecuteAsTestCommon):
    """Test cases for AuthExecuteAsController.

    Test flow:
    1. Authentication: API key validation, token expiry, client active
    2. Authorization: IP whitelist, method whitelist, user whitelist
    3. Execution: api.call_kw with @api.model and record methods
    4. Response: clean_response, field filtering, logging
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = AuthExecuteAsController()
        cls.request_path = "odoo.addons.auth_execute_as.controllers.main.request"

    def _mock_request(self, api_key=None, remote_addr="127.0.0.1"):
        """Create mock request with env and headers."""
        mock = MagicMock()
        mock.env = self.env
        mock.httprequest.headers.get.return_value = api_key
        mock.httprequest.remote_addr = remote_addr
        mock.httprequest.environ = {}
        del mock.get_json_data  # Force using kwargs
        return mock

    def _execute(
        self,
        api_key,
        login=None,
        model="res.partner",
        method="search_read",
        args=None,
        kwargs=None,
        remote_addr="127.0.0.1",
    ):
        """Execute controller method with mock request."""
        mock = self._mock_request(api_key=api_key, remote_addr=remote_addr)
        with patch(self.request_path, mock):
            return self.controller.execute_as(
                login=login or self.test_user.login,
                model=model,
                method=method,
                args=args if args is not None else [[]],
                kwargs=kwargs if kwargs is not None else {"limit": 1},
            )

    def _add_whitelist_method(self, method, **options):
        """Add method to whitelist with optional settings."""
        vals = {
            "whitelist_id": self.whitelist.id,
            "model_id": self.test_model.id,
            "method": method,
        }
        vals.update(options)
        return self.env["auth.api.whitelist.line"].create(vals)

    # ==================== 1. Authentication Tests (401) ====================

    def test_auth_01_missing_api_key(self):
        """Request without X-API-Key header returns 401."""
        result = self._execute(api_key=None)
        self.assertEqual(result["status_code"], 401)
        self.assertIn("Missing API Key", result["error"])

    def test_auth_02_invalid_api_key(self):
        """Request with non-existent API key returns 401."""
        result = self._execute(api_key="invalid_token_12345")
        self.assertEqual(result["status_code"], 401)
        self.assertIn("Invalid API Key", result["error"])

    def test_auth_03_expired_token(self):
        """Request with expired token returns 401."""
        self.client.token_expires_at = fields.Datetime.now() - timedelta(hours=1)
        result = self._execute(api_key=self.client.secret_token)
        self.assertEqual(result["status_code"], 401)
        self.assertIn("expired", result["error"])

    def test_auth_04_inactive_client(self):
        """Request with inactive client returns 401."""
        self.client.active = False
        result = self._execute(api_key=self.client.secret_token)
        self.assertEqual(result["status_code"], 401)
        self.assertIn("Invalid API Key", result["error"])

    # ==================== 2. Authorization Tests (403) ====================

    def test_authz_01_ip_not_allowed(self):
        """Request from non-allowed IP returns 403."""
        self.client.allowed_ips = "10.0.0.1, 192.168.0.0/24"
        result = self._execute(
            api_key=self.client.secret_token, remote_addr="172.16.0.1"
        )
        self.assertEqual(result["status_code"], 403)
        self.assertIn("not allowed", result["error"])

    def test_authz_02_ip_allowed_single(self):
        """Request from allowed single IP succeeds."""
        self.client.allowed_ips = "192.168.1.100"
        result = self._execute(
            api_key=self.client.secret_token, remote_addr="192.168.1.100"
        )
        self.assertIsInstance(result, list)

    def test_authz_03_ip_allowed_cidr(self):
        """Request from IP in CIDR range succeeds."""
        self.client.allowed_ips = "192.168.1.0/24"
        result = self._execute(
            api_key=self.client.secret_token, remote_addr="192.168.1.55"
        )
        self.assertIsInstance(result, list)

    def test_authz_04_method_not_whitelisted(self):
        """Request for non-whitelisted method returns 403."""
        result = self._execute(api_key=self.client.secret_token, method="unlink")
        self.assertEqual(result["status_code"], 403)
        self.assertIn("not allowed", result["error"])

    def test_authz_05_user_not_in_allowed_list(self):
        """Request to impersonate non-allowed user returns 403."""
        other_user = self.env["res.users"].create(
            {
                "name": "Other User",
                "login": "other@example.com",
            }
        )
        self.client.allowed_user_ids = [(6, 0, [self.test_user.id])]
        result = self._execute(api_key=self.client.secret_token, login=other_user.login)
        self.assertEqual(result["status_code"], 403)
        self.assertIn("not allowed", result["error"])

    def test_authz_06_user_in_allowed_list(self):
        """Request to impersonate allowed user succeeds."""
        self.client.allowed_user_ids = [(6, 0, [self.test_user.id])]
        result = self._execute(api_key=self.client.secret_token)
        self.assertIsInstance(result, list)

    def test_authz_07_user_not_in_allowed_group(self):
        """Request for user not in allowed group returns 403."""
        group = self.env["res.groups"].create({"name": "Restricted Group"})
        self.client.allowed_group_ids = [(6, 0, [group.id])]
        result = self._execute(api_key=self.client.secret_token)
        self.assertEqual(result["status_code"], 403)

    def test_authz_08_user_in_allowed_group(self):
        """Request for user in allowed group succeeds."""
        group = self.env["res.groups"].create({"name": "API Group"})
        self.test_user.groups_id = [(4, group.id)]
        self.client.allowed_group_ids = [(6, 0, [group.id])]
        result = self._execute(api_key=self.client.secret_token)
        self.assertIsInstance(result, list)

    def test_authz_09_private_method_rejected(self):
        """Private method (starting with _) is rejected."""
        self._add_whitelist_method("_compute_display_name")
        result = self._execute(
            api_key=self.client.secret_token,
            method="_compute_display_name",
            args=[],
            kwargs={},
        )
        # Private methods rejected by get_public_method (403) or api.call_kw (500)
        self.assertIn(result["status_code"], [403, 500])
        self.assertTrue(
            "Private" in result["error"] or "not allowed" in result["error"]
        )

    # ==================== 3. Not Found Tests (404) ====================

    def test_notfound_01_user_not_found(self):
        """Request with non-existent login returns 404."""
        result = self._execute(
            api_key=self.client.secret_token, login="nonexistent@example.com"
        )
        self.assertEqual(result["status_code"], 404)
        self.assertIn("not found", result["error"])

    def test_notfound_02_method_not_found(self):
        """Request for non-existent method on model returns error."""
        self._add_whitelist_method("nonexistent_method_xyz")
        result = self._execute(
            api_key=self.client.secret_token,
            method="nonexistent_method_xyz",
            args=[],
            kwargs={},
        )
        self.assertIn(result["status_code"], [403, 404])

    # ==================== 4. api.call_kw Tests ====================

    def test_callkw_01_search_read(self):
        """Test search_read method (setup in common)."""
        result = self._execute(api_key=self.client.secret_token)
        self.assertIsInstance(result, list)

    def test_callkw_02_create(self):
        """Test create method (@api.model_create_multi)."""
        self._add_whitelist_method("create")
        result = self._execute(
            api_key=self.client.secret_token,
            method="create",
            args=[{"name": "Created Partner"}],
            kwargs={},
        )
        self.assertIsInstance(result, int)
        partner = self.env["res.partner"].browse(result)
        self.assertEqual(partner.name, "Created Partner")

    def test_callkw_03_read_with_ids(self):
        """Test read method with specific IDs."""
        self._add_whitelist_method("read")
        partner = self.env["res.partner"].create(
            {"name": "Read Test", "email": "read@test.com"}
        )
        result = self._execute(
            api_key=self.client.secret_token,
            method="read",
            args=[[partner.id]],
            kwargs={"fields": ["name", "email"]},
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Read Test")
        self.assertEqual(result[0]["email"], "read@test.com")

    def test_callkw_04_write_with_ids(self):
        """Test write method on specific records."""
        self._add_whitelist_method("write")
        partner = self.env["res.partner"].create({"name": "Old Name"})
        result = self._execute(
            api_key=self.client.secret_token,
            method="write",
            args=[[partner.id], {"name": "New Name"}],
            kwargs={},
        )
        self.assertTrue(result)
        partner.invalidate_recordset()
        self.assertEqual(partner.name, "New Name")

    def test_callkw_05_action_on_record(self):
        """Test action method (action_archive) on record."""
        self._add_whitelist_method("action_archive")
        partner = self.env["res.partner"].create({"name": "To Archive"})
        self.assertTrue(partner.active)

        self._execute(
            api_key=self.client.secret_token,
            method="action_archive",
            args=[[partner.id]],
            kwargs={},
        )
        partner.invalidate_recordset()
        self.assertFalse(partner.active)

    def test_callkw_06_multiple_ids(self):
        """Test method on multiple records."""
        self._add_whitelist_method("write")
        p1 = self.env["res.partner"].create({"name": "P1"})
        p2 = self.env["res.partner"].create({"name": "P2"})

        self._execute(
            api_key=self.client.secret_token,
            method="write",
            args=[[p1.id, p2.id], {"ref": "BULK001"}],
            kwargs={},
        )
        p1.invalidate_recordset()
        p2.invalidate_recordset()
        self.assertEqual(p1.ref, "BULK001")
        self.assertEqual(p2.ref, "BULK001")

    def test_callkw_07_invalid_id_returns_empty(self):
        """Test read with non-existent ID returns empty list."""
        self._add_whitelist_method("read")
        result = self._execute(
            api_key=self.client.secret_token,
            method="read",
            args=[[999999999]],
            kwargs={"fields": ["name"]},
        )
        # Odoo read() with non-existent IDs returns empty list, not MissingError
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    # ==================== 5. Response Processing Tests ====================

    def test_response_01_clean_response_true(self):
        """clean_response=True: Many2one (id, name) becomes name string."""
        self.whitelist_line.clean_response = True
        parent = self.env["res.partner"].create({"name": "Parent Co"})
        child = self.env["res.partner"].create(
            {"name": "Child", "parent_id": parent.id}
        )

        result = self._execute(
            api_key=self.client.secret_token,
            args=[[["id", "=", child.id]]],
            kwargs={"fields": ["name", "parent_id"]},
        )
        self.assertEqual(result[0]["parent_id"], "Parent Co")

    def test_response_02_clean_response_false(self):
        """clean_response=False: Many2one keeps tuple (id, name)."""
        self.whitelist_line.clean_response = False
        parent = self.env["res.partner"].create({"name": "Parent Raw"})
        child = self.env["res.partner"].create(
            {"name": "Child Raw", "parent_id": parent.id}
        )

        result = self._execute(
            api_key=self.client.secret_token,
            args=[[["id", "=", child.id]]],
            kwargs={"fields": ["name", "parent_id"]},
        )
        self.assertIsInstance(result[0]["parent_id"], (list, tuple))
        self.assertEqual(result[0]["parent_id"][0], parent.id)
        self.assertEqual(result[0]["parent_id"][1], "Parent Raw")

    def test_response_03_field_filtering(self):
        """field_ids filter: only allowed fields returned."""
        name_field = self.env["ir.model.fields"].search(
            [("model_id", "=", self.test_model.id), ("name", "=", "name")], limit=1
        )
        self.whitelist_line.field_ids = [(6, 0, [name_field.id])]

        result = self._execute(
            api_key=self.client.secret_token,
            kwargs={"fields": ["name", "email", "phone"], "limit": 1},
        )
        if result:
            self.assertIn("name", result[0])
            self.assertNotIn("email", result[0])
            self.assertNotIn("phone", result[0])

    # ==================== 6. Logging Tests ====================

    def test_logging_01_log_created(self):
        """log_call=True: creates log entry with full info."""
        self.whitelist_line.log_call = True
        self.whitelist_line.log_response = True

        count_before = self.env["auth.api.log"].search_count([])
        self._execute(api_key=self.client.secret_token)
        count_after = self.env["auth.api.log"].search_count([])

        self.assertEqual(count_after, count_before + 1)

        log = self.env["auth.api.log"].search([], order="id desc", limit=1)
        self.assertEqual(log.client_id, self.client)
        self.assertEqual(log.user_id, self.test_user)
        self.assertEqual(log.model_name, "res.partner")
        self.assertEqual(log.method, "search_read")
        self.assertEqual(log.status_code, 200)
        self.assertTrue(log.response_payload)

    def test_logging_02_log_call_disabled(self):
        """log_call=False: no log entry created."""
        self.whitelist_line.log_call = False

        count_before = self.env["auth.api.log"].search_count([])
        self._execute(api_key=self.client.secret_token)
        count_after = self.env["auth.api.log"].search_count([])

        self.assertEqual(count_after, count_before)

    def test_logging_03_log_response_disabled(self):
        """log_response=False: log has no response_payload."""
        self.whitelist_line.log_call = True
        self.whitelist_line.log_response = False

        self._execute(api_key=self.client.secret_token)

        log = self.env["auth.api.log"].search([], order="id desc", limit=1)
        self.assertFalse(log.response_payload)

    # ==================== 7. Error Handling Tests ====================

    def test_error_01_access_error_returns_403(self):
        """AccessError during execution returns 403."""
        self._add_whitelist_method("read")

        mock = self._mock_request(api_key=self.client.secret_token)
        with patch(self.request_path, mock):
            with patch("odoo.api.call_kw", side_effect=AccessError("Access Denied")):
                result = self.controller.execute_as(
                    login=self.test_user.login,
                    model="res.partner",
                    method="read",
                    args=[[1]],
                    kwargs={},
                )

        self.assertEqual(result["status_code"], 403)
        self.assertIn("Access Denied", result["error"])
