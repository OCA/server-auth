# Copyright 2017 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from werkzeug.utils import redirect

from odoo import http
from odoo.exceptions import AccessDenied
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from ..models import res_authentication_attempt, res_users
from .common import CommonTests, logging, skip_unless_addons_installed

_logger = logging.getLogger(__name__)

GARBAGE_LOGGERS = (
    "werkzeug",
    res_authentication_attempt.__name__,
    res_users.__name__,
)


# Skip CSRF validation on tests
@patch(http.__name__ + ".WebRequest.validate_csrf", return_value=True)
# Skip specific browser forgery on redirections
@patch(http.__name__ + ".redirect_with_hash", side_effect=redirect)
# Faster tests without calls to geolocation API
# @patch(res_authentication_attempt.__name__ + ".urlopen", return_value="")
@tagged("post_install", "-at_install")
class BruteForceCase(CommonTests):
    def setUp(self):
        super(BruteForceCase, self).setUp()
        #  Set IP to default: 127.0.0.1
        self.create_fake_request()

    @skip_unless_addons_installed("web")
    @mute_logger(*GARBAGE_LOGGERS)
    def test_web_login_existing(self, *args):
        """Remote is banned with real user on web login form."""
        data1 = {
            "login": "test_user",
            "password": "1234",  # Wrong
        }
        # Make sure user is logged out
        self.url_open("/web/session/logout", timeout=30)
        # Fail 3 times
        for _ in range(3):
            response = self.url_open("/web/login", data1, 30)
            # If you fail, you get /web/login again
            self.assertTrue(
                response.url.endswith("/web/login"),
                "Unexpected URL %s" % response.url,
            )
        # test_user banned, demo not
        with self.cursor() as cr:
            env = self.env(cr)
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                ),
            )
            self.assertTrue(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    "demo",
                ),
            )
        # Now I know the password, but login is rejected too
        data1["password"] = self.good_password
        response = self.url_open("/web/login", data1, 30)
        self.assertTrue(
            response.url.endswith("/web/login"),
            "Unexpected URL %s" % response.url,
        )
        # IP has been banned, demo user cannot login
        with self.cursor() as cr:
            env = self.env(cr)
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    "demo",
                ),
            )
        # Attempts recorded
        with self.cursor() as cr:
            env = self.env(cr)
            failed = env["res.authentication.attempt"].search(
                [
                    ("result", "=", "failed"),
                    ("login", "=", data1["login"]),
                    ("remote", "=", "127.0.0.1"),
                ]
            )
            self.assertEqual(len(failed), 3)
            banned = env["res.authentication.attempt"].search(
                [
                    ("result", "=", "banned"),
                    ("remote", "=", "127.0.0.1"),
                ]
            )
            self.assertEqual(len(banned), 1)
            self.assertFalse(all(failed.mapped("whitelisted")))
            # Unban
            failed.action_whitelist_add()
            failed._compute_whitelisted()
            self.assertTrue(all(failed.mapped("whitelisted")))
        # Try good login, it should work now
        response = self.url_open("/web/login", data1, 30)
        self.assertTrue(response.url.endswith("/web"))

    @skip_unless_addons_installed("web")
    @mute_logger(*GARBAGE_LOGGERS)
    def test_web_login_existing_unbanned(self, *args):
        """Remote is banned with real user on web login form."""
        data1 = {
            "login": "test_user",
            "password": "1234",  # Wrong
        }
        # Make sure user is logged out
        self.url_open("/web/session/logout", timeout=30)
        # Fail 3 times
        for _ in range(3):
            response = self.url_open("/web/login", data1, 30)
            # If you fail, you get /web/login again
            self.assertTrue(
                response.url.endswith("/web/login"),
                "Unexpected URL %s" % response.url,
            )
        # test_user banned, demo not
        with self.cursor() as cr:
            env = self.env(cr)
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                ),
            )
            self.assertTrue(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    "demo",
                ),
            )
        # Now I know the password, but login is rejected too
        data1["password"] = self.good_password
        response = self.url_open("/web/login", data1, 30)
        self.assertTrue(
            response.url.endswith("/web/login"),
            "Unexpected URL %s" % response.url,
        )
        # IP has been banned, demo user cannot login
        with self.cursor() as cr:
            env = self.env(cr)
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    "demo",
                ),
            )
        # Attempts recorded
        with self.cursor() as cr:
            env = self.env(cr)
            failed = env["res.authentication.attempt"].search(
                [
                    ("result", "=", "failed"),
                    ("login", "=", data1["login"]),
                    ("remote", "=", "127.0.0.1"),
                ]
            )
            self.assertEqual(len(failed), 3)
            banned = env["res.authentication.attempt"].search(
                [
                    ("result", "=", "banned"),
                    ("remote", "=", "127.0.0.1"),
                ]
            )
            self.assertEqual(len(banned), 1)
            self.assertFalse(banned.whitelisted)
            # Unban
            banned.action_unban()
            self.assertFalse(banned.whitelisted)
        # Try good login, it should work now
        response = self.url_open("/web/login", data1, 30)
        self.assertTrue(response.url.endswith("/web"))

    @skip_unless_addons_installed("web")
    @mute_logger(*GARBAGE_LOGGERS)
    def test_web_login_unexisting(self, *args):
        """Remote is banned with fake user on web login form."""
        data1 = {
            "login": "administrator",  # Wrong
            "password": self.good_password,
        }
        # Make sure user is logged out
        self.url_open("/web/session/logout", timeout=30)
        # Fail 3 times
        for _ in range(3):
            response = self.url_open("/web/login", data1, 30)
            # If you fail, you get /web/login again
            self.assertTrue(
                response.url.endswith("/web/login"),
                "Unexpected URL %s" % response.url,
            )
        # test_user banned, demo not
        with self.cursor() as cr:
            env = self.env(cr)
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                ),
            )
            self.assertTrue(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    self.data_demo["login"],
                ),
            )
        # Demo user can login
        response = self.url_open("/web/login", self.data_demo, 30)
        # If you pass, you get /web
        self.assertTrue(
            response.url.endswith("/web"),
            "Unexpected URL %s" % response.url,
        )
        self.url_open("/web/session/logout", timeout=30)
        # Attempts recorded
        with self.cursor() as cr:
            env = self.env(cr)
            failed = env["res.authentication.attempt"].search(
                [
                    ("result", "=", "failed"),
                    ("login", "=", data1["login"]),
                    ("remote", "=", "127.0.0.1"),
                ]
            )
            self.assertEqual(len(failed), 3)
            banned = env["res.authentication.attempt"].search(
                [
                    ("result", "=", "banned"),
                    ("login", "=", data1["login"]),
                    ("remote", "=", "127.0.0.1"),
                ]
            )
            self.assertEqual(len(banned), 0)

    @mute_logger(*GARBAGE_LOGGERS)
    def test_orm_login_existing(self, *args):
        """No bans on ORM login with an existing user."""
        data1 = {
            "login": "test_user",
            "password": "1234",  # Wrong
        }
        with self.cursor() as cr:
            env = self.env(cr)
            # Fail 3 times
            for _ in range(3):
                with self.assertRaises(AccessDenied):
                    env["res.users"].authenticate(
                        cr.dbname, data1["login"], data1["password"], {}
                    )
            failed = env["res.authentication.attempt"].search(args=[])
            self.assertEqual(
                len(failed),
                3,
            )
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                ),
            )
            failed.action_whitelist_add()
            self.assertTrue(all(failed.mapped("whitelisted")))
            # Now I know the password, and login works
            data1["password"] = self.good_password
            self.assertIsInstance(
                env["res.users"].authenticate(
                    cr.dbname, data1["login"], data1["password"], {}
                ),
                int,
                "Access denied",
            )

    @mute_logger(*GARBAGE_LOGGERS)
    def test_action_whitelist_remove(self, *args):
        """Remove from whitelist and try login."""
        data1 = {
            "login": "test_user",  # Wrong
            "password": "1234",
        }
        with self.cursor() as cr:
            env = self.env(cr)
            # Fail 3 times
            for _ in range(3):
                with self.assertRaises(AccessDenied):
                    env["res.users"].authenticate(
                        cr.dbname, data1["login"], data1["password"], {}
                    )
            failed = env["res.authentication.attempt"].search(args=[])
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                ),
            )
            # Add to whitelist and check again we will get True this time.
            failed.action_whitelist_add()
            self.assertTrue(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                ),
            )
            # Remove ip from list and try login, It will generate Access Error.
            failed.action_whitelist_remove()
            data1["password"] = self.good_password
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                ),
            )
            with self.assertRaises(AccessDenied):
                env["res.users"].authenticate(
                    cr.dbname, data1["login"], data1["password"], {}
                )
            #  Check metadata of remote address
            # On internet loss it return False that's why bool instance check
            # self.assertTrue(all(failed.mapped('remote_metadata')))
            self.assertIsInstance(all(failed.mapped("remote_metadata")), bool)

    @mute_logger(*GARBAGE_LOGGERS)
    def test_orm_login_unexisting(self, *args):
        """No bans on ORM login with an unexisting user."""
        data1 = {
            "login": "administrator",  # Wrong
            "password": self.good_password,
        }
        with self.cursor() as cr:
            env = self.env(cr)
            # Fail 3 times
            for _ in range(3):
                with self.assertRaises(AccessDenied):
                    env["res.users"].authenticate(
                        cr.dbname, data1["login"], data1["password"], {}
                    )
            self.assertEqual(
                env["res.authentication.attempt"].search(count=True, args=[]),
                3,
            )
            # Now I know the user, and login works
            data1["login"] = "test_user"
            self.assertTrue(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                ),
            )
            self.assertIsInstance(
                env["res.users"].authenticate(
                    cr.dbname, data1["login"], data1["password"], {}
                ),
                int,
                "Access denied",
            )
