# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAuthSignupPartnerCompany(TransactionCase):
    def setUp(self):
        super(TestAuthSignupPartnerCompany, self).setUp()
        self.env["ir.config_parameter"].set_param("auth_signup.invitation_scope", "b2c")
        self.company = self.env.company
        self.company_jpy = self.env["res.company"].create(
            {
                "name": "Japan company",
                "currency_id": self.env.ref("base.JPY").id,
                "country_id": self.env.ref("base.jp").id,
            }
        )

    def test_auth_signpu_partner_company(self):
        self.env["res.users"].signup(
            {"name": "Test", "login": "test@gmail.com", "password": "12345678"}
        )
        user = self.env["res.users"].search([("login", "=", "test@gmail.com")])
        self.assertEqual(user.company_id, self.company)
        self.assertEqual(user.partner_id.company_id, self.company)

        self.env.company = self.company_jpy
        self.env["res.users"].signup(
            {"name": "Test1", "login": "test1@gmail.com", "password": "12345678"}
        )
        user = self.env["res.users"].search([("login", "=", "test1@gmail.com")])
        self.assertEqual(user.company_id, self.company_jpy)
        self.assertEqual(user.partner_id.company_id, self.company_jpy)
