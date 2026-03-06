import logging
import types

from odoo import api, models

from ..tools import crypto

_logger = logging.getLogger(__name__)


class EncryptionMixin(models.AbstractModel):
    _name = "encryption.mixin"
    _description = "Mixin to support encrypted fields"

    @api.model
    def _valid_field_parameter(self, field, name):
        """Tell Odoo that 'encrypted=True' is a valid parameter for fields on this model"""
        return name == "encrypted" or super()._valid_field_parameter(field, name)

    @api.model
    def _get_encrypted_fields(self):
        """Helper to retrieve all encrypted fields on the current model."""
        return [
            name
            for name, field in self._fields.items()
            if getattr(field, "encrypted", False)
        ]

    @api.model
    def _setup_complete(self):
        """
        Dynamically patch the `convert_to_record` method of fields marked as `encrypted=True`.
        This is the most reliable hook in Odoo 16 to intercept data just before it is returned
        to the Python application from the cache.
        """
        res = super()._setup_complete()

        for name, field in self._fields.items():
            if getattr(field, "encrypted", False) and not getattr(
                field, "_encrypted_patched", False
            ):
                _logger.info(
                    "Patching encrypted field '%s' on model '%s'", name, self._name
                )

                # Save original bound methods
                orig_convert_to_record = field.convert_to_record

                def new_convert_to_record(
                    self_field, value, record, _orig=orig_convert_to_record
                ):
                    # Standard Odoo conversion first
                    val = _orig(value, record)
                    # If it's an encrypted token, decrypt it before giving it to the python code
                    if val and isinstance(val, str) and val.startswith("gAAAAAB"):
                        return crypto.decrypt(val)
                    return val

                # Bind the new method to the field instance
                field.convert_to_record = types.MethodType(new_convert_to_record, field)
                field._encrypted_patched = True

        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Encrypt values on creation and prevent dummy value '********' from being saved."""
        encrypted_fields = self._get_encrypted_fields()
        if encrypted_fields:
            for vals in vals_list:
                for f in encrypted_fields:
                    val = vals.get(f)
                    if val == "********":
                        del vals[f]
                    elif val:
                        vals[f] = crypto.encrypt(val)
        return super().create(vals_list)

    def write(self, vals):
        """Encrypt values on write and prevent dummy value '********' from overwriting."""
        encrypted_fields = self._get_encrypted_fields()
        if encrypted_fields:
            for f in encrypted_fields:
                val = vals.get(f)
                if val == "********":
                    del vals[f]
                elif val:
                    vals[f] = crypto.encrypt(val)
            if not vals:
                return True
        return super().write(vals)

    def read(self, fields=None, load="_classic_read"):
        """
        Intercept public reads (e.g., from the web client).
        Replace the plaintext cache values with the dummy mask '********'.
        """
        res = super().read(fields, load)
        if not self.env.context.get("decrypt_fields"):
            encrypted_fields = self._get_encrypted_fields()
            if encrypted_fields:
                for rec in res:
                    for f in encrypted_fields:
                        if rec.get(f):
                            rec[f] = "********"
        return res
