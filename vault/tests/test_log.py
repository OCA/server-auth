# © 2021 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.base.tests.common import BaseCommon

_logger = logging.getLogger(__name__)


class TestLog(BaseCommon):
    def test_not_implemeneted(self):
        with self.assertRaises(NotImplementedError):
            self.env["vault.abstract"].log_entry("test")

        with self.assertRaises(NotImplementedError):
            self.env["vault.abstract"].log_info("test")

        with self.assertRaises(NotImplementedError):
            self.env["vault.abstract"].log_warn("test")

        with self.assertRaises(NotImplementedError):
            self.env["vault.abstract"].log_error("test")

    def test_log_created(self):
        vault = self.env["vault"].create({"name": "Vault"})
        entry = self.env["vault.entry"].create({"vault_id": vault.id, "name": "Entry"})

        vault.log_ids.unlink()

        vault.log_info("info")
        self.assertEqual(vault.log_ids.mapped("state"), ["info"])
        self.assertEqual(entry.log_ids.mapped("state"), [])

        entry.log_warn("warn")
        self.assertEqual(vault.log_ids.mapped("state"), ["info", "warn"])
        self.assertEqual(entry.log_ids.mapped("state"), ["warn"])

        entry.log_error("error")
        self.assertEqual(vault.log_ids.mapped("state"), ["info", "warn", "error"])
        self.assertEqual(entry.log_ids.mapped("state"), ["warn", "error"])
