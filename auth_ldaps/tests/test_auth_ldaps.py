# Copyright 2026 Studio73 - Ferran Mora <ferran@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import call, patch

import ldap

from odoo.tests.common import TransactionCase

from odoo.addons.auth_ldap.models.res_company_ldap import LDAPWrapper


class TestAuthLdaps(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["res.company.ldap"].create(
            {
                "company": cls.env.company.id,
                "ldap_server": "ldap.example.test",
                "ldap_server_port": 636,
                "ldap_base": "dc=example,dc=test",
                "ldap_filter": "(uid=%s)",
                "ldap_binddn": "cn=service,dc=example,dc=test",
                "ldap_password": "test-password",
                "is_ssl": True,
            }
        )
        cls.parameters = cls.env["ir.config_parameter"].sudo()

    def _configuration(self):
        return next(
            conf
            for conf in self.config._get_ldap_dicts()
            if conf["id"] == self.config.id
        )

    def test_ldaps_connection(self):
        conf = self._configuration()
        self.assertTrue(conf["is_ssl"])
        self.assertFalse(conf["skip_cert_validation"])
        self.parameters.search([("key", "=", "auth_ldap.disable_chase_ref")]).unlink()
        with patch(
            "odoo.addons.auth_ldaps.models.res_company_ldap.ldap.initialize"
        ) as initialize:
            connection = self.config._connect(conf)
            initialize.assert_called_once_with("ldaps://ldap.example.test:636")
            self.assertIsInstance(connection, LDAPWrapper)
            initialize.return_value.set_option.assert_called_once_with(
                ldap.OPT_REFERRALS, ldap.OPT_OFF
            )
            initialize.return_value.start_tls_s.assert_not_called()
            connection.simple_bind_s("test-dn", "test-password")
            connection.unbind()
            initialize.return_value.simple_bind_s.assert_called_once_with(
                "test-dn", "test-password"
            )
            initialize.return_value.unbind.assert_called_once_with()

    def test_explicit_options(self):
        # Explicit configuration takes precedence over the record's defaults.
        conf = dict(self._configuration(), skip_cert_validation=True, ldap_tls=True)
        self.parameters.set_param("auth_ldap.disable_chase_ref", "False")
        with patch(
            "odoo.addons.auth_ldaps.models.res_company_ldap.ldap.initialize"
        ) as initialize:
            self.env["res.company.ldap"]._connect(conf)
            self.assertEqual(
                initialize.return_value.method_calls,
                [
                    call.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW),
                    call.set_option(ldap.OPT_X_TLS_NEWCTX, 0),
                    call.start_tls_s(),
                ],
            )
        self.config.skip_cert_validation = True
        conf = self._configuration()
        conf["skip_cert_validation"] = False
        with patch(
            "odoo.addons.auth_ldaps.models.res_company_ldap.ldap.initialize"
        ) as initialize:
            self.config._connect(conf)
            initialize.return_value.set_option.assert_not_called()

    def test_standard_connection(self):
        conf = dict(self._configuration(), is_ssl=False)
        with patch(
            "odoo.addons.auth_ldap.models.res_company_ldap.ResCompanyLdap._connect"
        ) as connect:
            self.assertIs(self.config._connect(conf), connect.return_value)
            connect.assert_called_once_with(conf)

    def test_partial_configuration(self):
        conf = self._configuration()
        del conf["skip_cert_validation"]
        conf["is_ssl"] = False
        original = dict(conf)
        with patch(
            "odoo.addons.auth_ldap.models.res_company_ldap.ResCompanyLdap._connect"
        ) as connect:
            self.config._connect(conf)
            connect.assert_called_once_with(dict(conf, skip_cert_validation=False))
        self.assertEqual(conf, original)

    def test_connection_button(self):
        for is_ssl, scheme in [(True, "ldaps"), (False, "ldap")]:
            with self.subTest(is_ssl=is_ssl):
                self.config.is_ssl = is_ssl
                with patch(
                    "odoo.addons.auth_ldaps.models.res_company_ldap.ldap.initialize"
                ) as initialize:
                    result = self.config.test_ldap_connection()
                    self.assertEqual(result["params"]["type"], "success")
                    initialize.assert_called_once_with(
                        f"{scheme}://ldap.example.test:636"
                    )
                    initialize.return_value.simple_bind_s.assert_called_once_with(
                        self.config.ldap_binddn, self.config.ldap_password
                    )
                    initialize.return_value.unbind.assert_called_once_with()
        self.config.write({"is_ssl": True, "skip_cert_validation": True})
        with patch(
            "odoo.addons.auth_ldaps.models.res_company_ldap.ldap.initialize"
        ) as initialize:
            self.config.test_ldap_connection()
            initialize.return_value.set_option.assert_any_call(
                ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW
            )
            initialize.return_value.set_option.assert_any_call(ldap.OPT_X_TLS_NEWCTX, 0)

    def test_connection_button_errors(self):
        for error in [ldap.SERVER_DOWN, ldap.INVALID_CREDENTIALS]:
            with (
                self.subTest(error=error.__name__),
                patch(
                    "odoo.addons.auth_ldaps.models.res_company_ldap.ldap.initialize"
                ) as initialize,
            ):
                initialize.return_value.simple_bind_s.side_effect = error()
                result = self.config.test_ldap_connection()
                self.assertEqual(result["tag"], "display_notification")
                self.assertEqual(result["params"]["type"], "danger")

    def test_authentication(self):
        conf = self._configuration()
        entry = ("uid=test,dc=example,dc=test", {"cn": [b"Test User"]})
        with patch(
            "odoo.addons.auth_ldaps.models.res_company_ldap.ldap.initialize"
        ) as initialize:
            initialize.return_value.search_st.return_value = [entry]
            self.assertEqual(self.config._authenticate(conf, "test", "password"), entry)
            self.assertEqual(
                initialize.return_value.simple_bind_s.call_args_list,
                [
                    call(self.config.ldap_binddn, self.config.ldap_password),
                    call(entry[0], "password"),
                ],
            )
            self.assertEqual(initialize.return_value.unbind.call_count, 2)
