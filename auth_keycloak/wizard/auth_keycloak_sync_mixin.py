# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging
from json.decoder import JSONDecodeError

import requests

from odoo import _, exceptions, fields, models

logger = logging.getLogger(__name__)

KEYCLOAK_TIMEOUT = 60


class KeycloakSyncMixin(models.AbstractModel):
    """Synchronize Keycloak users mixin."""

    _name = "auth.keycloak.sync.mixin"

    provider_id = fields.Many2one(
        string="Provider",
        comodel_name="auth.oauth.provider",
        required=True,
    )
    management_enabled = fields.Boolean(
        related="provider_id.users_management_enabled",
        readonly=True,
    )
    endpoint = fields.Char(
        related="provider_id.users_endpoint",
        readonly=True,
    )
    user = fields.Char(
        related="provider_id.superuser",
        readonly=True,
    )
    pwd = fields.Char(
        related="provider_id.superuser_pwd",
        readonly=True,
    )
    # tech field to map unique key from Keycloak to Odoo
    login_match_key = fields.Selection(
        selection=[
            # keycloak:odoo
            ("username:login", "username"),
            ("email:partner_id.email", "email"),
        ],
        help="Keycloak user field to match users' login.",
        default="username:login",
    )

    def _validate_setup(self):
        """Make sure we are ready to talk to Keycloak."""
        self.ensure_one()
        if not self.management_enabled:
            raise exceptions.UserError(
                _("Users management must be enabled on selected provider")
            )

    def _validate_response(self, resp, no_json=False):
        """Make sure Keycloak answered properly."""
        if not resp.ok:
            # TODO: do something better?
            raise resp.raise_for_status()
        if no_json:
            return resp.content
        try:
            return resp.json()
        except JSONDecodeError as error:
            raise exceptions.UserError(
                _("Something went wrong. Please check logs.")
            ) from error

    def _get_token(self):
        """Retrieve auth token from Keycloak."""
        url = self.provider_id.token_endpoint
        logger.info("Calling %s" % url)
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "username": self.user,
            "password": self.pwd,
            "grant_type": "password",
            "client_id": self.provider_id.client_id,
            "client_secret": self.provider_id.client_secret,
        }
        resp = requests.post(url, data=data, headers=headers, timeout=KEYCLOAK_TIMEOUT)
        self._validate_response(resp)
        return resp.json()["access_token"]

    def _get_users(self, token, **params):
        """Retrieve users from Keycloak.

        :param token: a valida auth token from Keycloak
        :param **params: extra search params for users endpoint
        """
        logger.info("Calling %s" % self.endpoint)
        headers = {
            "Authorization": "Bearer %s" % token,
        }
        resp = requests.get(
            self.endpoint, headers=headers, params=params, timeout=KEYCLOAK_TIMEOUT
        )
        self._validate_response(resp)
        return resp.json()

    def _get_odoo_users(self, logins):
        """Retrieve odoo users matching given login values."""
        odoo_key = self.login_match_key.split(":")[-1]
        domain = [("oauth_uid", "=", False), (odoo_key, "in", logins)]
        return self.env["res.users"].search(domain)
