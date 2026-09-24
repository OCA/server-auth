# Copyright © 2025 XCG SAS
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.web.tests.test_login import TestWebLoginCommon


class TestWebLogin(TestWebLoginCommon):
    def test_web_logout(self):
        self.login("internal_user", "internal_user")
        res = self.url_open("/web/session/logout")
        self.assertEqual(res.request.path_url, "/web/logout_successful")

    def test_web_logout_page_while_logged_in(self):
        self.login("internal_user", "internal_user")
        res = self.url_open("/web/logout_successful")
        self.assertEqual(res.request.path_url, "/web/logout_successful")
