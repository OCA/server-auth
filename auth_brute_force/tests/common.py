import logging
from unittest.mock import Mock

import odoo
from odoo.exceptions import AccessDenied
from odoo.sql_db import TestCursor
from odoo.tests.common import HttpCase
from odoo.tools import DotDict

from ..models import res_authentication_attempt, res_users

_logger = logging.getLogger(__name__)

GARBAGE_LOGGERS = (
    "werkzeug",
    res_authentication_attempt.__name__,
    res_users.__name__,
)


def exit_func(self, exc_type, exc_value, traceback):
    """
    When AccessDenied is raised TestCursor.__exit__() would normally
    close and rollback cursor to previous point. Patch __exit__ so that
    tests that intentionally raise AccessDenied don't lose the DB state
    expected for assertions (commit instead of rollback in those cases).
    """
    try:
        # commit on normal exit or AccessDenied to keep DB state for tests
        if exc_type is None or isinstance(exc_value, AccessDenied):
            self.commit()
    finally:
        self.close()


# Patch TestCursor.__exit__ for test environment
TestCursor.__exit__ = exit_func


class CommonTests(HttpCase):
    def setUp(self):
        super().setUp()
        # Some tests could retain environ from last test and produce fake
        # results without this patch
        self.create_fake_request()
        self.good_password = "Admin$%02584"
        self.data_demo = {
            "login": "demo",
            "password": "Demo%&/(908409**",
            "type": "password",
        }
        self.env["res.users"].create(
            {
                "login": "test_user",
                "password": self.good_password,
                "name": "test_user User",
            }
        )

        with self.cursor() as cr:
            env = self.env(cr)
            env["ir.config_parameter"].set_param("auth_brute_force.max_by_ip_user", 3)
            env["ir.config_parameter"].set_param("auth_brute_force.max_by_ip", 4)
            self.env["ir.config_parameter"].set_param(
                "auth_brute_force.whitelist_remotes", ""
            )
            # Clean attempts to be able to count in tests
            env["res.authentication.attempt"].search([]).unlink()

    def create_fake_request(self, ip="127.0.0.1"):
        """Push a fake request onto the request stack so code that reads
        odoo.http.request will find expected attributes (ip, headers, etc.)."""
        environ = {
            "REMOTE_ADDR": ip,
            "HTTP_REFERER": "referer",
            "HTTP_USER_AGENT": "user agent",
            "HTTP_ACCEPT_LANGUAGE": "Language",
        }
        request = Mock(
            context={},
            db=self.env.cr.dbname,
            uid=None,
            httprequest=Mock(environ=environ, host=""),
            session=DotDict(),
            env=self.env,
            cr=self.env.cr,
        )
        odoo.http._request_stack.push(request)
        self.addCleanup(odoo.http._request_stack.pop)

    def url_open(self, url, data=None, timeout=10):
        PORT = odoo.tools.config["http_port"]
        HOST = "127.0.0.1"
        if url.startswith("/"):
            url = f"http://{HOST}:{PORT}{url}"
        if data:
            return self.opener.post(url, data=data, timeout=timeout)
        return self.opener.get(url, timeout=timeout)
