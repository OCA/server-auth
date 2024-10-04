
from odoo import Command
from odoo.tests.common import HttpCase, tagged
from odoo.addons.auth_password_pwned.controllers import test_controllers


@tagged('-at_install', 'post_install', 'auth_password_pwned')
class TestPwnedPasswords(HttpCase):

    def setUp(self):
        super(TestPwnedPasswords, self).setUp()
        self.env['ir.config_parameter'].set_param("auth_password_pwned.range_url", "http://localhost:8069/auth_password_pwned/range/")
        test_controllers.KNOWN_HASHES.clear()

    def test_login_with_pwned_password(self):
        return
        self.env["res.users"].create(
            {
                "login": "testpassword",
                "password": "testpassword",
                "name": "my test user with unsafe password",
                "groups_id": [Command.link(self.env.ref("base.group_user").id)],
            }
        )
        test_controllers.KNOWN_HASHES += ["8BB6118F8FD6935AD0876A3BE34A717D32708FFD"] # sha1sum of testpassword
        self.start_tour("/web/login","auth_password_pwned/static/tests/tours/login_test_tour_pwned.js", login="testpassword")

    def test_login_with_ok_password(self):
        return
        self.env["res.users"].create(
            {
                "login": "testuser",
                "password": "testuser",
                "name": "my test user with safe password",
                "groups_id": [Command.link(self.env.ref("base.group_user").id)],
            }
        )
        self.start_tour("/web/login","auth_password_pwned/static/tests/tours/login_test_tour_ok.js", login="testuser")

    def test_backend_password_pwned_backend(self):
        test_controllers.KNOWN_HASHES += ["89E495E7941CF9E40E6980D14A16BF023CCD4C91"]  # sha1sum of demo
        self.start_tour("/web", "auth_password_pwned/static/tests/tours/change_password_test_tour_pwned.js", login="admin")

    def test_backend_changing_ok_password(self):
        # TODO
        pass
