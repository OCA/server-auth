# Copyright 2022 Braintec AG
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTOTP(HttpCase):
    def test_totp(self):
        # Création d'un utilisateur de test (pas de données de démo en CI)
        test_user = self.env["res.users"].create(
            {
                "login": "test_totp_user",
                "name": "Test TOTP User",
                "password": "!asdQWE12345_3",
            }
        )
        uid = test_user.id

        self.authenticate(user="test_totp_user", password="!asdQWE12345_3")
        self.assertEqual(self.session.uid, uid)

        self.assertEqual(test_user._password_has_expired(), False)
        self.assertEqual(test_user.partner_id.signup_type, False)
        test_user.action_expire_password()
        self.assertEqual(test_user.partner_id.signup_type, "reset")

        self.logout()
        self.assertNotEqual(self.session.uid, uid)
