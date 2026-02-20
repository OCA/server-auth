# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

import requests

from odoo import _, exceptions, fields, models

from .auth_keycloak_sync_mixin import KEYCLOAK_TIMEOUT

logger = logging.getLogger(__name__)


class KeycloakCreateWiz(models.TransientModel):
    """Export Odoo users to Keycloak.

    Usually Keycloak is already populated w/ your users base.
    Many times this will come via LDAP, AD, pick yours.

    Still, you might need to push some users to Keycloak on demand,
    maybe just for testing.

    If you need this, this is the wizard for you ;)
    """

    _name = "auth.keycloak.create.wiz"
    _inherit = "auth.keycloak.sync.mixin"

    user_ids = fields.Many2many(
        comodel_name="res.users",
        default=lambda self: self.env.context.get("active_ids"),
    )

    def _validate_setup(self):
        if not self.user_ids:
            raise exceptions.UserError(_("No user selected"))
        return super()._validate_setup()

    def _validate_response(self, resp, no_json=False):
        # When Keycloak detects a clash on non-unique values, like emails,
        # it raises:
        # `HTTPError: 409 Client Error: Conflict for url: `
        # http://keycloak:8080/auth/admin/realms/master/users
        if resp.status_code == 409:
            detail = ""
            if resp.content and resp.json().get("errorMessage"):
                # ie: {"errorMessage":"User exists with same username"}
                detail = "\n" + resp.json().get("errorMessage")
            raise exceptions.UserError(
                _(
                    "Conflict on user values. "
                    "Please verify that all values supposed to be unique "
                    "are really unique. %(detail)s"
                )
                % {"detail": detail}
            )
        return super()._validate_response(resp, no_json=no_json)

    def _get_or_create_user(self, token, odoo_user):
        """Lookup for given user on Keycloak: create it if missing.

        :param token: valid auth token from Keycloak
        :param odoo_user: res.users record
        """
        odoo_key = self.login_match_key.split(":")[1]
        keycloak_user = self._get_users(token, search=odoo_user.mapped(odoo_key)[0])
        if keycloak_user:
            if len(keycloak_user) > 1:
                # TODO: warn user?
                pass
            return keycloak_user[0]
        else:
            values = self._create_user_values(odoo_user)
            keycloak_user = self._create_user(token, **values)
        return keycloak_user

    def _create_user_values(self, odoo_user):
        """Prepare Keycloak values for given Odoo user."""
        values = {
            "username": odoo_user.login,
            "email": odoo_user.email,
            "emailVerified": True,
            "enabled": True,
        }
        if "firstname" in odoo_user.partner_id:
            # partner_firstname installed
            firstname = odoo_user.partner_id.firstname
            lastname = odoo_user.partner_id.lastname
        else:
            firstname, lastname = self._split_user_fullname(odoo_user)
        values.update(
            {
                "firstName": firstname,
                "lastName": lastname,
            }
        )
        logger.debug("CREATE using values %s" % str(values))
        return values

    def _split_user_fullname(self, odoo_user):
        # yeah, I know, it's not perfect... you can override it ;)
        name_parts = odoo_user.name.split(" ")
        if len(name_parts) == 2:
            # great we've found the 2 parts
            firstname, lastname = name_parts
        else:
            # make sure firstname is there
            # then use the rest - if any - to build lastname
            firstname, lastname = name_parts[0], " ".join(name_parts[1:])
        return firstname, lastname

    def _create_user(self, token, **data):
        """Create a user on Keycloak w/ given data."""
        logger.info("CREATE Calling %s" % self.endpoint)
        headers = {
            "Authorization": "Bearer %s" % token,
        }
        # TODO: what to do w/ credentials?
        # Shall we just rely on Keycloak sending out a reset password link?
        # Shall we enforce a dummy pwd and enable "change after 1st login"?
        resp = requests.post(
            self.endpoint, headers=headers, json=data, timeout=KEYCLOAK_TIMEOUT
        )
        self._validate_response(resp, no_json=True)
        # yes, Keycloak sends back NOTHING on create
        # so we are forced to do anothe call to get its data :(
        return self._get_users(token, search=data["username"])[0]

    def button_create_user(self):
        """Create users on Keycloak.

        1. get a token
        2. loop on given users
        3. push them to Keycloak if:
           a. missing on Keycloak
           b. they do not have an Oauth UID already
        4. brings you to update users list
        """
        logger.debug("Create keycloak user START")
        self._validate_setup()
        token = self._get_token()
        logger.info("Creating users for %s" % ",".join(self.user_ids.mapped("login")))
        for user in self.user_ids:
            if user.oauth_uid:
                # already sync'ed somewhere else
                continue
            keycloak_user = self._get_or_create_user(token, user)
            user.update(
                {
                    "oauth_uid": keycloak_user["id"],
                    "oauth_provider_id": self.provider_id.id,
                }
            )
        action = self.env.ref("base.action_res_users").read()[0]
        action["domain"] = [("id", "in", self.user_ids.ids)]
        logger.debug("Create keycloak users STOP")
        return action
