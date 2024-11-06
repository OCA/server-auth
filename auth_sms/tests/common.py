# Copyright 2019-2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import HttpCase, new_test_user


class HttpCaseSMS(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref("base.user_admin")
        cls.username = "dportier"
        cls.password = "!asdQWE12345_3"  # strong password
        cls.demo_user = cls._create_user()
        cls.code = None
        cls.secret = None

    @classmethod
    def _create_user(cls):
        """Create auth_sms_enabled user."""
        return new_test_user(
            cls.env,
            login=cls.username,
            context={"no_reset_password": True},
            password=cls.password,
            name="Auth SMS test user",
            mobile="0123456789",
            email="auth_sms_test_user@yourcompany.com",
            auth_sms_enabled=True,
        )
