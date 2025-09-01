# Copyright (C) 2010-2016, 2022 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os

from odoo.tests import TransactionCase

from .fake_idp import FakeIDP


class TestUnsolicitedRequests(TransactionCase):
    def setUp(self):
        super().setUp()

        with open(
            os.path.join(os.path.dirname(__file__), "data", "sp.pem"),
            encoding="UTF-8",
        ) as file:
            sp_pem_public = file.read()

        with open(
            os.path.join(os.path.dirname(__file__), "data", "sp.key"),
            encoding="UTF-8",
        ) as file:
            sp_pem_private = file.read()

        self.saml_provider = self.env["auth.saml.provider"].create(
            {
                "name": "SAML Provider Demo",
                "idp_metadata": FakeIDP().get_metadata(),
                "sp_pem_public": base64.b64encode(sp_pem_public.encode()),
                "sp_pem_private": base64.b64encode(sp_pem_private.encode()),
                "body": "Login with Provider",
                "active": True,
                "sig_alg": "SIG_RSA_SHA1",
                "matching_attribute": "mail",
            }
        )

    def test_unsolicited_request_setting_default_false(self):
        """Test that unsolicited requests are disabled by default"""
        # Default company setting should be False
        self.assertFalse(self.env.company.allow_saml_unsolicited_req)

        # Provider computed field should reflect company setting
        self.assertFalse(self.saml_provider.allow_saml_unsolicited_req)

    def test_unsolicited_request_setting_enabled(self):
        """Test enabling unsolicited requests"""
        # Enable unsolicited requests for company
        self.env.company.allow_saml_unsolicited_req = True

        # Provider computed field should reflect the change
        self.saml_provider._compute_allow_saml_unsolicited()
        self.assertTrue(self.saml_provider.allow_saml_unsolicited_req)

    def test_saml_config_with_unsolicited_enabled(self):
        """Test that SAML configuration includes unsolicited setting"""
        # Enable unsolicited requests
        self.env.company.allow_saml_unsolicited_req = True
        self.saml_provider._compute_allow_saml_unsolicited()

        # Get SAML config
        config = self.saml_provider._get_config_for_provider()

        # Check that the config includes the allow_unsolicited setting
        sp_config = config.getattr("service", "sp")
        self.assertTrue(sp_config.get("allow_unsolicited"))

    def test_saml_config_with_unsolicited_disabled(self):
        """Test that SAML configuration respects disabled unsolicited setting"""
        # Ensure unsolicited requests are disabled
        self.env.company.allow_saml_unsolicited_req = False
        self.saml_provider._compute_allow_saml_unsolicited()

        # Get SAML config
        config = self.saml_provider._get_config_for_provider()

        # Check that the config does not allow unsolicited requests
        sp_config = config.getattr("service", "sp")
        self.assertFalse(sp_config.get("allow_unsolicited"))
