import logging
from unittest.mock import Mock

from decorator import decorator

import odoo
from odoo.exceptions import AccessDenied
from odoo.sql_db import TestCursor
from odoo.tests.common import HttpCase
from odoo.tools import DotDict
from odoo.http import request

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
            try:
                self.commit()
            except Exception:
                # Be defensive: commit may fail on closed cursor etc.
                pass
    finally:
        try:
            self.close()
        except Exception:
            pass


# Patch TestCursor.__exit__ for test environment
TestCursor.__exit__ = exit_func


# # HACK https://github.com/odoo/odoo/pull/24833
# def skip_unless_addons_installed(*addons):
#     """Decorator to skip a test unless some addons are installed.
#     :param *str addons:
#         Addon names that should be installed.
#     :param reason:
#         Explain why you must skip this test.
#     """

#     @decorator
#     def _wrapper(method, self, *args, **kwargs):
#         installed = self.addons_installed(*addons)
#         if not installed:
#             missing = set(addons) - set(installed.mapped("name"))
#             self.skipTest(
#                 "Required addons not installed: %s" % ",".join(sorted(missing))
#             )
#         return method(self, *args, **kwargs)

#     return _wrapper


class CommonTests(HttpCase):
    def setUp(self):
        super(CommonTests, self).setUp()
        # Some tests could retain environ from last test and produce fake
        # results without this patch
        self.create_fake_request()
        self.good_password = "Admin$%02584"
        self.data_demo = {
            "login": "demo",
            "password": "Demo%&/(908409**",
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
            # print('\n\n env 1111111111111', env)
            # print('\n env.user 22222222222222', env.user)
            env["ir.config_parameter"].set_param("auth_brute_force.max_by_ip_user", 3)
            env["ir.config_parameter"].set_param("auth_brute_force.max_by_ip", 4)
            self.env["ir.config_parameter"].set_param(
                "auth_brute_force.whitelist_remotes", ""
            )
            # Clean attempts to be able to count in tests
            env["res.authentication.attempt"].search([]).unlink()
# #Custom Code Commented
#             user = env.user
#             user["password"] = self.good_password
#             # env.user.password = self.good_password
#             print('\n env.user.password 333333333333', env.user.password)
#             env["res.users"].search(
#                 [
#                     ("login", "=", self.data_demo["login"]),
#                 ]
#             ).password = self.data_demo["password"]
# #Custom Code Commented

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
            url = "http://%s:%s%s" % (HOST, PORT, url)
        if data:
            return self.opener.post(url, data=data, timeout=timeout)
        return self.opener.get(url, timeout=timeout)

    # HACK https://github.com/odoo/odoo/pull/24833
    def addons_installed(self, *addons):
        """Know if the specified addons are installed."""
        found = self.env["ir.module.module"].search(
            [
                ("name", "in", addons),
                ("state", "not in", ["uninstalled", "uninstallable"]),
            ]
        )
        # return set(addons) - set(found.mapped("name"))
        return found
