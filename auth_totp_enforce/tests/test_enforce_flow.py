# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import re
import time

from odoo.tests import HttpCase, get_db_name, new_test_user, tagged
from odoo.tools import mute_logger

from odoo.addons.auth_totp.models.totp import TIMESTEP, hotp


@tagged("post_install", "-at_install")
class TestEnforceFlow(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.enforced = new_test_user(
            cls.env,
            login="flow_enforced",
            password="flow_enforced_pwd",
            tz="UTC",
        )
        cls.exempt = new_test_user(
            cls.env,
            login="flow_exempt",
            password="flow_exempt_pwd",
            tz="UTC",
            groups="base.group_user,auth_totp_enforce.group_mfa_exempt",
        )

    def _password_login(self, login, password):
        # POST to the JSON auth endpoint and return the ``result`` dict
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 0,
            "params": {"db": get_db_name(), "login": login, "password": password},
        }
        response = self.url_open(
            "/web/session/authenticate",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        return response.json()["result"]

    @mute_logger("odoo.http")
    def test_enforced_user_is_held_before_backend(self):
        # Enforced user must not be fully logged in until 2FA is set up
        result = self._password_login("flow_enforced", "flow_enforced_pwd")
        self.assertIsNone(result["uid"])

    def test_exempt_user_logs_in_directly(self):
        # Exempt user must reach the backend without any 2FA step
        result = self._password_login("flow_exempt", "flow_exempt_pwd")
        self.assertEqual(result["uid"], self.exempt.id)

    @mute_logger("odoo.http")
    def test_setup_page_activates_and_hands_off_to_standard_step(self):
        # Password step -> partial session (blocked)
        u_id = self._password_login("flow_enforced", "flow_enforced_pwd")["uid"]
        self.assertIsNone(u_id)
        # The mandatory setup page is served on the partial session
        page = self.url_open("/web/login/totp/setup")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Set up MFA", page.text)
        # Read the generated secret and CSRF token off the page
        sec = re.search(r"<code[^>]*>\s*([A-Z2-7 ]+?)\s*</code>", page.text).group(1)
        csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text).group(1)
        # Submit a valid code computed from that secret
        key = base64.b32decode(sec.replace(" ", ""))
        code = hotp(key, int(time.time() / TIMESTEP))
        response_data = {"totp_token": str(code), "csrf_token": csrf}
        response = self.url_open("/web/login/totp/setup", data=response_data)
        self.assertEqual(response.status_code, 200)
        # The secret is now stored on the user
        self.enforced.invalidate_recordset(["totp_secret", "totp_enabled"])
        self.assertTrue(self.enforced.totp_enabled)
        # We were redirected to standard MFA (still not logged in)
        self.assertNotIn("Set up MFA", response.text)
        self.assertIn("Authentication Code", response.text)

    def test_setup_page_redirects_when_no_partial_session(self):
        # Setup URL without a pre-authenticated session bounce back to login page
        response = self.url_open("/web/login/totp/setup", allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        # Location may be absolute (http://host/web/login) or relative.
        location = response.headers.get("Location", "")
        self.assertTrue(location.endswith("/web/login"))
