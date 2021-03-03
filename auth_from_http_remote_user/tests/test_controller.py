# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import SingleTransactionCase
from ..controllers.main import Home


class TestController(SingleTransactionCase):

    def setUp(self):
        self.home = Home()

    def test_search_user(self):
        u = self.home.search_user(self.env['res.users'], 'admin')
        self.assertTrue(u)
        u = self.home.search_user(self.env['res.users'], 'admin_unknown_user')
        self.assertFalse(u)

    def test_login_http_remote_user(self):
        key = self.home.login_http_remote_user(self.env, self.env.user)
        self.assertTrue(key)
