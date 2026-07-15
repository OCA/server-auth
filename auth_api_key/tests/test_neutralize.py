# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.modules import neutralize
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "neutralize")
class TestAuthApiKeyNeutralize(TransactionCase):
    def test_neutralize_removes_api_key_values(self):
        """Test database neutralization clears stored API key secrets."""
        api_key = self.env["auth.api.key"].create(
            {
                "name": "neutralize",
                "user_id": self.env.ref("base.user_admin").id,
                "key": "secret-key",
            }
        )

        queries = neutralize.get_neutralization_queries(["auth_api_key"])
        for query in queries:
            self.cr.execute(query)
        api_key.invalidate_recordset(["key"])
        self.assertFalse(api_key.key)
