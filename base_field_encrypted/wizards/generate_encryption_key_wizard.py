# Copyright 2026 Antonio Ruban
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from cryptography.fernet import Fernet

from odoo import fields, models


class GenerateEncryptionKeyWizard(models.TransientModel):
    _name = "generate.encryption.key.wizard"
    _description = "Generate Encryption Key Wizard"

    # The key is computed dynamically and never stored in the database
    key = fields.Char(
        string="New Encryption Key",
        compute="_compute_key",
        store=False,
        readonly=True,
        help=(
            "Copy this key and paste it into your odoo.conf file. "
            "It will never be saved in the database."
        ),
    )

    message = fields.Text(
        string="Instructions",
        default=(
            "1. Copy the generated key above.\n"
            "2. Paste it into your odoo.conf file under the [options] section:\n\n"
            "[options]\n"
            "encryption_key = PASTE_THE_KEY_HERE\n\n"
            "3. Restart your Odoo server.\n\n"
            "⚠️ IMPORTANT: This key is dynamically generated in memory and "
            "NEVER touches the database. If you lose it and had encrypted data, "
            "that data will be lost forever!"
        ),
        readonly=True,
        store=False,
    )

    def _compute_key(self):
        for record in self:
            # Generate a new key on the fly every time the record is read
            record.key = Fernet.generate_key().decode()

    def action_regenerate(self):
        """Forces a refresh of the wizard to compute a new key."""
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
