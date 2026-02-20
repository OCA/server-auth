# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from odoo import models

logger = logging.getLogger(__name__)


class KeycloakSyncWiz(models.TransientModel):
    """Synchronize Keycloak users to Odoo.

    Keycloak auth works w/ its internal ID stored into `sub` key.
    Auth from Odoo will not work if Odoo users do not have this key stored.

    This wizard takes care of this
    so that your existing users will be able to login.

    This is not an issue for new users as they are sync'ed at signup.
    """

    _name = "auth.keycloak.sync.wiz"
    _inherit = "auth.keycloak.sync.mixin"

    def button_sync(self):
        """Sync Keycloak users w/ Odoo users.

        1. get a token
        2. retrieve ALL users
        3. find matching Odoo users
        4. update them w/ their own Keycloak ID
        5. get back to filtered list of updated users
        """
        logger.info("Sync keycloak users START")
        self._validate_setup()
        token = self._get_token()
        users = self._get_users(token)
        logger.info("Found %s Keycloak users" % len(users))
        # map users by match key
        keycloak_key, odoo_key = self.login_match_key.split(":")
        logins_mapping = {x[keycloak_key]: x for x in users if x.get(keycloak_key)}
        logins = list(logins_mapping.keys())
        # find matching odoo users
        odoo_users = self._get_odoo_users(logins)
        logger.info("Matching %s Odoo users" % len(odoo_users))
        # update odoo users
        for user in odoo_users:
            # use `mapped` since we cann acces nested records
            keykloak_user = logins_mapping[user.mapped(odoo_key)[0]]
            # oh yeah, when you call `/userinfo` you get `sub` key
            # when you call `/users` you get `id` :S
            user.update(
                {
                    "oauth_uid": keykloak_user["id"],
                    "oauth_provider_id": self.provider_id.id,
                }
            )
        # open users' tree view
        action = self.env.ref("base.action_res_users").read()[0]
        action["domain"] = [("id", "in", odoo_users.ids)]
        logger.info("Sync keycloak users STOP")
        return action
