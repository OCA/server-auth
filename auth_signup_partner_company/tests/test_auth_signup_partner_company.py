# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAuthSignupPartnerCompany(TransactionCase):
    def setUp(self):
        super(TestAuthSignupPartnerCompany, self).setUp()
        self.env["ir.config_parameter"].set_param("auth_signup.invitation_scope", "b2c")
        self.company_1 = self.env.company
        self.company_2 = self.env["res.company"].create({"name": "company 2"})

    def test_auth_signup_company(self):
        self.assertEqual(self.env.company, self.company_1)
        self.env["res.users"].signup(
            {"name": "test 1", "login": "test1@gmail.com", "password": "12345678"}
        )
        user = self.env["res.users"].search([("login", "=", "test1@gmail.com")])
        self.assertEqual(user.company_id, self.company_1)
        self.assertEqual(user.partner_id.company_id, self.company_1)
        # Switch to another company and sign up.
        self.env.company = self.company_2
        self.env["res.users"].signup(
            {"name": "test 2", "login": "test2@gmail.com", "password": "12345678"}
        )
        user = self.env["res.users"].search([("login", "=", "test2@gmail.com")])
        self.assertEqual(user.company_id, self.company_2)
        self.assertEqual(user.partner_id.company_id, self.company_2)
