# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import datetime
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL

from odoo.addons.base.models.res_users import INDEX_SIZE, KEY_CRYPT_CONTEXT

_logger = logging.getLogger(__name__)


class ResUsersApikeys(models.Model):
    # Backport of odoo/odoo#178558 (18.0)

    _inherit = "res.users.apikeys"

    expiration_date = fields.Datetime(readonly=True)

    def init(self):
        res = super().init()
        self.env.cr.execute(
            SQL(
                "ALTER TABLE %s ADD COLUMN IF NOT EXISTS expiration_date"
                " timestamp without time zone",
                SQL.identifier(self._table),
            )
        )
        return res

    def _check_credentials(self, *, scope, key):
        # refuse the expired keys (18.0 filters them in the query)
        self.env.cr.execute(
            SQL(
                "SELECT key FROM %s WHERE index = %s"
                " AND expiration_date < now() at time zone 'utc'",
                SQL.identifier(self._table),
                key[:INDEX_SIZE],
            )
        )
        if any(
            KEY_CRYPT_CONTEXT.verify(key, expired_key)
            for (expired_key,) in self.env.cr.fetchall()
        ):
            return None
        return super()._check_credentials(scope=scope, key=key)

    def _check_expiration_date(self, date):
        # To be in a sudoed environment or to be an administrator
        # to create a persistent key (no expiration date) or
        # to exceed the maximum duration determined by the user's privileges.
        if self.env.is_system():
            return
        if not date:
            raise ValidationError(_("The API key must have an expiration date"))
        max_duration = (
            max(group.api_key_duration for group in self.env.user.groups_id) or 1.0
        )
        if date > fields.Datetime.now() + datetime.timedelta(days=max_duration):
            raise ValidationError(
                _("You cannot exceed %(duration)s days.", duration=max_duration)
            )

    def _generate(self, scope, name):
        # 18.0 adds an expiration_date parameter, but the 17.0 overrides only
        # take scope and name: the date comes from the context instead.
        # Call in sudo to exceed the groups' maximum duration, or without
        # date for a persistent key.
        expiration_date = self.env.context.get("api_key_expiration_date")
        # auth_totp.device inherits this model, but its 17.0 callers pass no
        # expiration date: the date is only required for the API keys
        if self._name == "res.users.apikeys":
            self._check_expiration_date(expiration_date)
        key = super()._generate(scope, name)
        if expiration_date:
            self.env.cr.execute(
                SQL(
                    """
                    UPDATE %(table)s SET expiration_date = %(date)s
                    WHERE id = (
                        SELECT id FROM %(table)s
                        WHERE index = %(index)s AND user_id = %(uid)s
                        ORDER BY id DESC LIMIT 1
                    )
                    """,
                    table=SQL.identifier(self._table),
                    date=expiration_date,
                    index=key[:INDEX_SIZE],
                    uid=self.env.uid,
                )
            )
            self.invalidate_model(["expiration_date"])
        return key

    @api.autovacuum
    def _gc_user_apikeys(self):
        self.env.cr.execute(
            SQL(
                """
                DELETE FROM %s
                WHERE
                    expiration_date IS NOT NULL AND
                    expiration_date < now() at time zone 'utc'
                """,
                SQL.identifier(self._table),
            )
        )
        _logger.info("GC %r delete %d entries", self._name, self.env.cr.rowcount)
