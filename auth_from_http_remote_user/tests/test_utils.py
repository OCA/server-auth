# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import re
from odoo.tests.common import SingleTransactionCase
from .. import utils


class TestUtils(SingleTransactionCase):

    def setUp(self):
        super().setUp()
        self.reo = re.compile(r'^[0-9]*$')

    def test_corret_randomString(self):
        """Test that random string generator.

        Making sure that it uses only the char specified
        And it is of the correct length
        """
        allowed_char = '1234567890'
        s = utils.randomString(16, allowed_char)
        self.assertEqual(len(s), 16)
        self.assertTrue(self.reo.match(s))
