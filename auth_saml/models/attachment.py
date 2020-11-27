import base64
from odoo import models


class Attachment(models.Model):
    _inherit = "ir.attachment"

    def _save_to_file_system(self):
        value = self.datas
        bin_data = base64.b64decode(value) if value else b''
        checksum = self._compute_checksum(bin_data)
        self.store_fname = self._file_write(value, checksum)
