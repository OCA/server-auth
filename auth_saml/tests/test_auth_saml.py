# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common

from .util.odoo_tests import TestBase
from .util.singleton import Singleton


class TestMemory(object):
    """Keep records in memory across tests."""

    __metaclass__ = Singleton


@common.at_install(False)
@common.post_install(True)
class Test(TestBase):
    def setUp(self):
        super(Test, self).setUp()
        self.memory = TestMemory()

    # TODO Tests.
