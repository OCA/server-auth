# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

import jwt

from odoo import tests


@tests.tagged("post_install", "-at_install")
class TestRegisterHook(tests.HttpCase):
    def test_auth_method_exists(self):
        validator = self.env["auth.jwt.validator"].search([("name", "=", "demo")])
        self.assertEqual(len(validator), 1)
        self.assertTrue(hasattr(self.env["ir.http"].__class__, "_auth_method_jwt_demo"))

    def _get_token(self, aud=None, email=None):
        validator = self.env["auth.jwt.validator"].search([("name", "=", "demo")])
        payload = {
            "aud": aud or validator.audience,
            "iss": validator.issuer,
            "exp": time.time() + 60,
        }
        if email:
            payload["email"] = email
        access_token = jwt.encode(
            payload, key=validator.secret_key, algorithm=validator.secret_algorithm
        )
        return "Bearer " + access_token

    def test_whoami(self):
        """A end-to-end test with positive authentication and partner retrieval."""
        partner = self.env["res.users"].search([("email", "!=", False)])[0]
        token = self._get_token(email=partner.email)
        resp = self.url_open("/auth_jwt_demo/whoami", headers={"Authorization": token})
        resp.raise_for_status()
        whoami = resp.json()
        self.assertEqual(whoami.get("name"), partner.name)
        self.assertEqual(whoami.get("email"), partner.email)
        # Try again in a user session, it will be rejected because auth_jwt
        # is not designed to work in user session.
        self.authenticate("demo", "demo")
        resp = self.url_open("/auth_jwt_demo/whoami", headers={"Authorization": token})
        self.assertEqual(resp.status_code, 401)

    def test_forbidden(self):
        """A end-to-end test with negative authentication."""
        token = self._get_token(aud="invalid")
        resp = self.url_open("/auth_jwt_demo/whoami", headers={"Authorization": token})
        self.assertEqual(resp.status_code, 401)
