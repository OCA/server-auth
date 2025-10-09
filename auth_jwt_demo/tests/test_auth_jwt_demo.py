# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import time

import jwt

from odoo import tests


@tests.tagged("post_install", "-at_install")
class TestRegisterHook(tests.HttpCase):
    def test_auth_method_exists(self):
        validator = self.env["auth.jwt.validator"].search([("name", "=", "demo")])
        self.assertEqual(len(validator), 1)
        self.assertTrue(hasattr(self.env["ir.http"].__class__, "_auth_method_jwt_demo"))


@tests.tagged("post_install", "-at_install")
class TestEndToEnd(tests.HttpCase):
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
        self.assertEqual(whoami.get("uid"), self.env.ref("base.user_demo").id)
        # Try again in a user session, it will be rejected because auth_jwt
        # is not designed to work in user session.
        self.authenticate("demo", "demo")
        with self.assertLogs("odoo.addons.auth_jwt.models.ir_http", "WARNING") as logs:
            resp = self.url_open(
                "/auth_jwt_demo/whoami", headers={"Authorization": token}
            )
            self.assertEqual(len(logs.records), 1)
            self.assertEqual(logs.records[0].levelno, logging.WARNING)
            self.assertIn(
                'A route with auth="jwt" must not be used within a user session',
                logs.output[0],
            )
        self.assertEqual(resp.status_code, 401)

    def test_whoami_cookie(self):
        """A end-to-end test with positive authentication and cookie."""
        partner = self.env["res.users"].search([("email", "!=", False)])[0]
        token = self._get_token(email=partner.email)
        resp = self.url_open(
            "/auth_jwt_demo_cookie/whoami", headers={"Authorization": token}
        )
        resp.raise_for_status()
        whoami = resp.json()
        self.assertEqual(whoami.get("name"), partner.name)
        self.assertEqual(whoami.get("email"), partner.email)
        self.assertEqual(whoami.get("uid"), self.env.ref("base.user_demo").id)
        cookie = resp.cookies.get("demo_auth")
        self.assertTrue(cookie)
        # Try again with the cookie.
        resp = self.url_open(
            "/auth_jwt_demo_cookie/whoami", headers={"Cookie": f"demo_auth={cookie}"}
        )
        resp.raise_for_status()
        whoami = resp.json()
        self.assertEqual(whoami.get("name"), partner.name)
        self.assertEqual(whoami.get("email"), partner.email)
        self.assertEqual(whoami.get("uid"), self.env.ref("base.user_demo").id)
        cookie = resp.cookies.get("demo_auth")
        self.assertTrue(cookie)

    def test_forbidden(self):
        """A end-to-end test with negative authentication."""
        token = self._get_token(aud="invalid")
        resp = self.url_open("/auth_jwt_demo/whoami", headers={"Authorization": token})
        self.assertEqual(resp.status_code, 401)

    def test_public(self):
        """A end-to-end test for anonymous/public access."""
        resp = self.url_open("/auth_jwt_demo/whoami-public-or-jwt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["uid"], self.ref("base.public_user"))
        # try with a token for an non-existing partner, auth works
        # but we don't get any partner info
        token = self._get_token(email="not-a-partner@example.com")
        resp = self.url_open(
            "/auth_jwt_demo/whoami-public-or-jwt", headers={"Authorization": token}
        )
        self.assertEqual(resp.status_code, 200)
        resp.raise_for_status()
        whoami = resp.json()
        self.assertTrue("name" not in whoami)
        self.assertTrue("email" not in whoami)
        self.assertEqual(whoami.get("uid"), self.env.ref("base.user_demo").id)
        # now try with a token
        partner = self.env["res.users"].search([("email", "!=", False)], limit=1)
        token = self._get_token(email=partner.email)
        resp = self.url_open(
            "/auth_jwt_demo/whoami-public-or-jwt", headers={"Authorization": token}
        )
        resp.raise_for_status()
        whoami = resp.json()
        self.assertEqual(whoami.get("name"), partner.name)
        self.assertEqual(whoami.get("email"), partner.email)
        self.assertEqual(whoami.get("uid"), self.env.ref("base.user_demo").id)

    def test_public_cookie_mode(self):
        """A end-to-end test for anonymous/public access with cookie."""
        resp = self.url_open("/auth_jwt_demo_cookie/whoami-public-or-jwt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["uid"], self.ref("base.public_user"))
        cookie = resp.cookies.get("demo_auth")
        self.assertFalse(cookie)
        # try with a token for an non-existing partner, auth works
        # but we don't get any partner info
        token = self._get_token(email="not-a-partner@example.com")
        resp = self.url_open(
            "/auth_jwt_demo_cookie/whoami-public-or-jwt",
            headers={"Authorization": token},
        )
        resp.raise_for_status()
        whoami = resp.json()
        self.assertTrue("name" not in whoami)
        self.assertTrue("email" not in whoami)
        self.assertEqual(whoami.get("uid"), self.env.ref("base.user_demo").id)
        cookie = resp.cookies.get("demo_auth")
        self.assertTrue(cookie)
        # now try with a token
        partner = self.env["res.users"].search([("email", "!=", False)], limit=1)
        token = self._get_token(email=partner.email)
        resp = self.url_open(
            "/auth_jwt_demo_cookie/whoami-public-or-jwt",
            headers={"Authorization": token},
        )
        resp.raise_for_status()
        whoami = resp.json()
        self.assertEqual(whoami.get("name"), partner.name)
        self.assertEqual(whoami.get("email"), partner.email)
        self.assertEqual(whoami.get("uid"), self.env.ref("base.user_demo").id)
        # now try with the cookie
        cookie = resp.cookies.get("demo_auth")
        self.assertTrue(cookie)
        partner = self.env["res.users"].search([("email", "!=", False)], limit=1)
        token = self._get_token(email=partner.email)
        resp = self.url_open(
            "/auth_jwt_demo_cookie/whoami-public-or-jwt",
            headers={"Cookie": f"demo_auth={cookie}"},
        )
        resp.raise_for_status()
        whoami = resp.json()
        self.assertEqual(whoami.get("name"), partner.name)
        self.assertEqual(whoami.get("email"), partner.email)
        self.assertEqual(whoami.get("uid"), self.env.ref("base.user_demo").id)
        cookie = resp.cookies.get("demo_auth")
        self.assertTrue(cookie)

    def test_public_keyloak(self):
        """A end-to-end test for anonymous/public access."""
        resp = self.url_open("/auth_jwt_demo/keycloak/whoami-public-or-jwt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["uid"], self.ref("base.public_user"))
