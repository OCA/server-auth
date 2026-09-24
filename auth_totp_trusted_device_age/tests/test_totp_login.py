# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import os
import re
import time

from odoo import http
from odoo.tests import HttpCase, tagged

from odoo.addons.auth_totp.models.totp import TIMESTEP, hotp

from .common import DAY, TrustedDeviceCommon


@tagged("post_install", "-at_install")
class TestTotpLogin(TrustedDeviceCommon, HttpCase):
    def _login_with_device(self, key):
        """Pass the password step, then open the 2FA step from a trusted browser"""
        self.authenticate(None, None)
        self.session.pre_uid = self.user.id
        self.session.pre_login = self.user.login
        http.root.session_store.save(self.session)
        self.opener.cookies["td_id"] = key
        return self.url_open("/web/login/totp", allow_redirects=False)

    def _session_uid(self, response):
        sid = response.cookies.get("session_id", self.session.sid)
        return http.root.session_store.get(sid).uid

    def test_trusted_device_skips_2fa(self):
        response = self._login_with_device(self._new_device())
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self._session_uid(response), self.user.id)

    def test_expired_device_asks_2fa(self):
        response = self._login_with_device(self._new_device(expired=True))
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="totp_token"', response.text)
        self.assertFalse(self._session_uid(response))

    def test_remember_device_cookie_age(self):
        """The cookie of a new trusted device lasts the trusted device age"""
        self.env["ir.config_parameter"].set_param("auth_totp.trusted_device_age", 180)
        secret = base64.b32encode(os.urandom(20)).decode()
        self.user.sudo().totp_secret = secret
        self.authenticate(None, None)
        self.session.pre_uid = self.user.id
        self.session.pre_login = self.user.login
        http.root.session_store.save(self.session)
        form = self.url_open("/web/login/totp").text
        csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', form).group(1)
        token = hotp(base64.b32decode(secret), int(time.time() / TIMESTEP))
        response = self.url_open(
            "/web/login/totp",
            data={"csrf_token": csrf_token, "totp_token": f"{token:06}", "remember": 1},
            # the name of the device is built from the browser
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Firefox/140.0"},
            allow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        cookies = [
            cookie
            for cookie in response.raw.headers.getlist("Set-Cookie")
            if cookie.startswith("td_id=")
        ]
        self.assertEqual(len(cookies), 1)
        self.assertIn(f"Max-Age={180 * DAY}", cookies[0])
        self.assertTrue(self._devices())
