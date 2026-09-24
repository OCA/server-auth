# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

TRUSTED_DEVICE_AGE_DAYS = 90


class AuthTotpDevice(models.Model):
    _inherit = "auth_totp.device"

    def _get_trusted_device_age(self):
        # backport of odoo/odoo#205500 (19.0)
        icp = self.env["ir.config_parameter"].sudo()
        try:
            nbr_days = int(
                icp.get_param("auth_totp.trusted_device_age", TRUSTED_DEVICE_AGE_DAYS)
            )
            if nbr_days <= 0:
                nbr_days = None
        except ValueError:
            nbr_days = None

        if nbr_days is None:
            _logger.warning(
                "Invalid value for 'auth_totp.trusted_device_age', using default value."
            )
            nbr_days = TRUSTED_DEVICE_AGE_DAYS

        return nbr_days * 86400  # seconds

    def _generate(self, scope, name):
        # the 17.0 auth_totp controller calls _generate(scope, name): the
        # expiration date is passed to base_api_key_expiration in the context
        self = self.with_context(
            api_key_expiration_date=fields.Datetime.now()
            + timedelta(seconds=self._get_trusted_device_age())
        )
        return super()._generate(scope, name)

    @api.autovacuum
    def _gc_device(self):
        # 17.0 removes the devices created more than 90 days ago: only do it
        # for the devices without expiration date, the others are removed
        # once expired by the autovacuum of base_api_key_expiration
        self.env.cr.execute(
            SQL(
                "DELETE FROM %s WHERE expiration_date IS NULL"
                " AND create_date < (NOW() AT TIME ZONE 'UTC') - %s * INTERVAL '1 day'",
                SQL.identifier(self._table),
                TRUSTED_DEVICE_AGE_DAYS,
            )
        )
        _logger.info("GC'd %d totp devices entries", self.env.cr.rowcount)
