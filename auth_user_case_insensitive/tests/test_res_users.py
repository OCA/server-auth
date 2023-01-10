# Copyright 2015-2017 LasLabs Inc.
# Copyright 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    def setUp(self):
        super(TestResUsers, self).setUp()
        self.login = "LasLabs@ExAmPlE.CoM"
        self.partner_vals = {
            "name": "Partner",
            "is_company": False,
            "email": self.login,
        }
        self.vals = {"name": "User", "login": self.login, "password": "password"}
        self.model_obj = self.env["res.users"]

    def _new_record(self):
        """Gnerate a new record to test with."""
        partner_id = self.env["res.partner"].create(self.partner_vals)
        self.vals["partner_id"] = partner_id.id
        return self.model_obj.create(self.vals)

    def test_login_is_lowercased_on_create(self):
        """Verify the login is set to lowercase on create."""
        rec_id = self._new_record()
        self.assertEqual(
            self.login.lower(),
            rec_id.login,
            "Login was not lowercased when saved to db.",
        )

    def test_login_is_lowercased_on_write(self):
        """Verify the login is set to lowercase on write."""
        rec_id = self._new_record()
        rec_id.write({"login": self.login})
        self.assertEqual(
            self.login.lower(),
            rec_id.login,
            "Login was not lowercased when saved to db.",
        )

    def test_login_login_is_lowercased(self):
        """verify the login is set to lowercase on login."""
        rec_id = self.model_obj.search([("login", "=", "admin")])
        res_id = self.model_obj._login(
            self.env.registry.db_name,
            "AdMiN",
            "admin",
            {"interactive": True},
        )
        self.assertEqual(
            rec_id.id,
            res_id,
            "Login with with uppercase chars was not \
            successful",
        )
