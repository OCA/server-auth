# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, new_test_user


class TestPasswordHistory(TransactionCase):
    def setUp(self):
        super().setUp()
        self.username = "jackoneill"
        self.passwd = "!asdQWE12345_3"
        self.user = new_test_user(self.env, self.username, password=self.passwd)

    def test_01_history_is_saved(self):
        """Doit sauvegarder l'historique des mots de passe."""
        self.assertEqual(len(self.user.password_history_ids), 1)
        self.user.password = "!asdQWE12345_4"
        self.user.invalidate_recordset()
        self.assertEqual(len(self.user.password_history_ids), 2)

    def test_02_history_is_limited(self):
        """Doit limiter la vérification à l'historique configuré."""
        self.env["ir.config_parameter"].sudo().set_param("password_security.history", 1)
        self.user.password = "!asdQWE12345_4"
        # Forcer le rafraîchissement du cache ORM après _set_encrypted_password
        self.user.invalidate_recordset()
        # Le premier mot de passe n'est plus dans l'historique actif (history=1)
        self.user.password = self.passwd

    def test_03_history_disabled(self):
        """Doit désactiver la vérification d'historique si history=0."""
        self.env["ir.config_parameter"].sudo().set_param("password_security.history", 0)
        self.user.password = self.passwd

    def test_04_history_unlimited(self):
        """Doit vérifier tout l'historique si history=-1."""
        self.env["ir.config_parameter"].sudo().set_param(
            "password_security.history", -1
        )
        with self.assertRaises(UserError):
            self.user.password = self.passwd
