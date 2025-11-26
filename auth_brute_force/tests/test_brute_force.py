from unittest.mock import patch

from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from ..models import res_authentication_attempt, res_users
from .common import CommonTests, logging

_logger = logging.getLogger(__name__)

GARBAGE_LOGGERS = (
    "werkzeug",
    res_authentication_attempt.__name__,
    res_users.__name__,
)


# Skip CSRF validation on tests
@patch("odoo.http.Request.validate_csrf", lambda self: True)
@tagged("post_install", "-at_install")
class BruteForceCase(CommonTests):
    def setUp(self):
        super().setUp()
        #  Set IP to default: 127.0.0.1
        self.create_fake_request()

    def authenticate_login(self, cr, env, num_of_times, data):
        for _ in range(num_of_times):
            try:
                env["res.users"].authenticate(
                    cr.dbname,
                    data,
                    {"interactive": True},  # , "REMOTE_ADDR": "127.0.0.1"
                )
            except AccessDenied:
                continue

    @mute_logger(*GARBAGE_LOGGERS)
    def test_web_login_existing(self, *args):
        """Remote is banned with real user on web login form."""
        data1 = {
            "login": "test_user",
            "password": "1234",  # Wrong
            "type": "password",
        }

        # Make sure user is logged out
        self.url_open("/web/session/logout", timeout=30)

        # 1) 3 failed attempts → only test_user banned
        with self.cursor() as cr:
            env = self.env(cr)
            request.params.update({"login": "test_user"})
            self.authenticate_login(cr, env, 3, data1)
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                )
            )
            self.assertTrue(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    "demo",
                )
            )
            self.authenticate_login(cr, env, 1, data1)
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    "demo",
                )
            )

        # 2) Fix password and check records
        data1["password"] = self.good_password

        # Attempts recorded
        with self.cursor() as cr:
            env = self.env(cr)
            failed = env["res.authentication.attempt"].search(
                [
                    ("result", "=", "failed"),
                    ("login", "=", data1["login"]),
                    ("remote", "=", "127.0.0.1"),
                ],
                limit=3,
            )
            self.assertEqual(len(failed), 3)
            self.assertFalse(all(failed.mapped("whitelisted")))
            # Unban
            failed.action_whitelist_add()
            failed._compute_whitelisted()
            self.assertTrue(all(failed.mapped("whitelisted")))

            self.authenticate_login(cr, env, 1, data1)
            # Create banned record
            env["res.authentication.attempt"].create(
                {
                    "result": "banned",
                    "login": data1["login"],
                    "remote": "127.0.0.1",
                }
            )
            banned = env["res.authentication.attempt"].search(
                [
                    ("result", "=", "banned"),
                    ("remote", "=", "127.0.0.1"),
                ],
                limit=1,
            )
            self.assertEqual(len(banned), 1)
            # Unban
            banned.action_unban()
            self.authenticate_login(cr, env, 1, data1)

    @mute_logger(*GARBAGE_LOGGERS)
    def test_web_login_unexisting(self, *args):
        """Remote is banned with fake user on web login form."""
        data1 = {
            "login": "test_user",
            "password": "1234",  # Wrong
            "type": "password",
        }

        # Make sure user is logged out
        self.url_open("/web/session/logout", timeout=30)

        # test_user banned, demo not
        with self.cursor() as cr:
            env = self.env(cr)
            # Fail 3 times
            self.authenticate_login(cr, env, 3, data1)
            auth = env["res.authentication.attempt"]._trusted(
                "127.0.0.1",
                data1["login"],
            )
            self.assertFalse(
                # If tuple → take first element
                auth[0] if isinstance(auth, tuple) else auth
            )
            self.assertTrue(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    self.data_demo["login"],
                ),
            )
            self.authenticate_login(cr, env, 1, self.data_demo)
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
            "type": "password",
        }
        with self.cursor() as cr:
            env = self.env(cr)
            # Fail 3 times
            with self.assertRaises(AccessDenied):
                env["res.users"].authenticate(
                    cr.dbname,
                    data1,
                    {"interactive": True},
                )
            for _ in range(3):
                try:
                    env["res.users"].authenticate(
                        cr.dbname,
                        data1,
                        {"interactive": True},
                    )
                except AccessDenied:
                    # _logger.info("AccessError with login: {}".format(data1['login']))
                    continue
            failed = env["res.authentication.attempt"].search([])
            self.assertEqual(
                len(failed),
                3,
            )
            self.assertFalse(
                env["res.authentication.attempt"]._trusted(
                    "127.0.0.1",
                    data1["login"],
                )
            )
            failed.action_whitelist_add()
            self.assertTrue(all(failed.mapped("whitelisted")))
            # Now I know the password, and login works
            data1["password"] = self.good_password

            result = env["res.users"].authenticate(
                cr.dbname,
                data1,
                {"interactive": True},
            )
            self.assertIsInstance(result, dict)

    @mute_logger(*GARBAGE_LOGGERS)
    def test_action_whitelist_remove(self, *args):
        """Remove from whitelist and try login."""
        data1 = {
            "login": "test_user",  # Wrong
            "password": "1234",
            "type": "password",
        }
        with self.cursor() as cr:
            env = self.env(cr)
            # Fail 3 times
            with self.assertRaises(AccessDenied):
                env["res.users"].authenticate(
                    cr.dbname,
                    data1,
                    {"interactive": True},
                )
            for _ in range(3):
                try:
                    env["res.users"].authenticate(
                        cr.dbname,
                        data1,
                        {"interactive": True},
                    )
                except AccessDenied:
                    # _logger.info("AccessError with login: {}".format(data1['login']))
                    continue
            failed = env["res.authentication.attempt"].search([])
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
                    cr.dbname,
                    data1,
                    {"interactive": True},
                )
            try:
                env["res.users"].authenticate(
                    cr.dbname,
                    data1,
                    {"interactive": True},
                )
            except AccessDenied:
                _logger.info("AccessError with login: {}".format(data1["login"]))
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
            "type": "password",
        }
        with self.cursor() as cr:
            env = self.env(cr)
            # Fail 3 times
            with self.assertRaises(AccessDenied):
                env["res.users"].authenticate(
                    cr.dbname,
                    data1,
                    {"interactive": True},
                )
            for _ in range(3):
                try:
                    env["res.users"].authenticate(
                        cr.dbname,
                        data1,
                        {"interactive": True},
                    )
                except AccessDenied:
                    # _logger.info("AccessError with login: {}".format(data1['login']))
                    continue
            self.assertEqual(
                env["res.authentication.attempt"].search_count([]),
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
                    cr.dbname,
                    data1,
                    {"interactive": True},
                ),
                dict,
                "Access denied",
            )
