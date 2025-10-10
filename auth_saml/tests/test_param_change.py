from odoo.tests.common import TransactionCase


class TestParamChange(TransactionCase):
    def test_set_param(self):
        """Changing the parameter should go through without error"""
        self.env["ir.config_parameter"].set_param(
            "auth_saml.allow_saml_uid_and_internal_password",
            False,
        )
