from odoo.tests.common import HttpCase
from odoo import http
from threading import current_thread
from mock import patch
from werkzeug.utils import redirect
import time


# Skip CSRF validation on tests
@patch(http.__name__ + ".WebRequest.validate_csrf", return_value=True)
# Skip specific browser forgery on redirections
@patch(http.__name__ + ".redirect_with_hash", side_effect=redirect)
# Faster tests without calls to geolocation API
class TestWebLogin(HttpCase):
    def setUp(self):
        super().setUp()
        # Some tests could retain environ from last test and produce fake
        # results without this patch
        # HACK https://github.com/odoo/odoo/issues/24183
        # TODO Remove in v12
        try:
            del current_thread().environ
        except AttributeError:
            pass
        # Complex password to avoid conflicts with `password_security`
        self.data = {
            "login": "admin",
            "password": "admin",
        }
        self.timeout = False
        with self.cursor() as cr:
            env = self.env(cr)
            self.timeout = env[
                "ir.config_parameter"]._auth_timeout_get_parameter_delay()
            env["ir.config_parameter"].set_param(
                "inactive_session_time_out_delay", 10)

    def test_login(self, *args):
        try:
            self.url_open("/web/session/logout", timeout=30)
            response = self.url_open("/web/login", self.data, 30)
            self.assertTrue(
                response.url.endswith("/web"),
                "Unexpected URL %s" % response.url,
            )
            self.assertTrue(response.cookies.get('session_id'))
            self.assertTrue(http.root.session_store.get(
                response.cookies.get('session_id')).update_time)
            self.assertTrue(http.root.session_store.get(
                response.cookies.get('session_id')).uid)
            response = self.url_open("/web", timeout=30)
            self.assertTrue(
                response.url.endswith("/web"),
                "Unexpected URL %s" % response.url,
            )
            self.assertTrue(response.cookies.get('session_id'))
            self.assertTrue(http.root.session_store.get(
                response.cookies.get('session_id')).uid)
            time.sleep(11)
            response = self.url_open("/web", timeout=30)
            self.assertTrue(response.cookies.get('session_id'))
            self.assertFalse(http.root.session_store.get(
                response.cookies.get('session_id')).uid)
        except Exception:
            raise
        finally:
            with self.cursor() as cr:
                env = self.env(cr)
                # 15 seconds of timeout is not much, so it is necessary to
                # change it back.
                env["ir.config_parameter"].set_param(
                    "inactive_session_time_out_delay", self.timeout)
