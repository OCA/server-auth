# -*- coding: utf-8 -*-
# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from .common_test_controller import OAuthProviderControllerTransactionCase
from .common_test_oauth_provider_controller import \
    TestOAuthProviderUserinfoController, \
    TestOAuthProviderOtherinfoController, \
    TestOAuthProviderRevokeTokenController

_logger = logging.getLogger(__name__)


class TestOAuthProviderController(
        OAuthProviderControllerTransactionCase,
        TestOAuthProviderUserinfoController,
        TestOAuthProviderOtherinfoController,
        TestOAuthProviderRevokeTokenController):
    def setUp(self):
        super().setUp('backend application')
