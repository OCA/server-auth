from odoo.tests.common import TransactionCase


class TestGenerateSignupValues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {"name": "Test user", "login": "testuser"}
        )

    def test_generate_signup_values_no_login(self):
        provider_id = 1
        name = "Toto Le Héro"
        email = "toto@example.com"
        validation = {
            "user_id": "1234567890",
            "name": name,
            "email": email,
        }
        params = {
            "access_token": "thetoken",
        }
        res = self.user._generate_signup_values(provider_id, validation, params)
        self.assertEqual(res["name"], name)
        # Odoo's auth_oauth module sets login = email
        self.assertTrue(res["login"] == res["email"])

    def test_generate_signup_values_login(self):
        provider_id = 1
        name = "Toto Le Héro"
        email = "toto.externe@example.com"
        login = "toto@example.com"
        validation = {
            "user_id": "1234567890",
            "name": name,
            "email": email,
            "login": login,
        }
        params = {
            "access_token": "thetoken",
        }
        res = self.user._generate_signup_values(provider_id, validation, params)
        self.assertEqual(res["name"], name)
        # With this module we can have a different login than email
        self.assertTrue(res["login"] != res["email"])
        self.assertEqual(res["login"], login)
        self.assertEqual(res["email"], email)
