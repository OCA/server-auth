# Copyright 2023 Paja SIA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.exceptions import AccessDenied
from odoo.tests.common import TransactionCase

from odoo.addons.auth_signup.models.res_partner import SignupError


class TestOAuthSignup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env.ref("auth_oauth.provider_google")
        cls.env["ir.config_parameter"].set_param("auth_signup.invitation_scope", "b2b")
        cls.params = {
            "oauth_provider_id": cls.provider.id,
            "access_token": "ACCESS_TOKEN",
            "state": "{}",
        }
        cls.validation = {
            "user_id": "UID",
            "email": "example@example.com",
            "name": "Example",
        }

    def test_signup_not_allowed(self):
        self.provider.allow_signup = False
        with self.assertRaises(AccessDenied):
            self.env["res.users"]._auth_oauth_signin(
                self.provider.id, self.validation, self.params
            )

    def test_signup_allowed(self):
        self.provider.allow_signup = True
        self.env["res.users"]._auth_oauth_signin(
            self.provider.id, self.validation, self.params
        )

    def test_no_provider_signup_error(self):
        with self.assertRaises(SignupError):
            self.env["res.users"]._signup_create_user({"invalidfield": "invalidvalue"})
