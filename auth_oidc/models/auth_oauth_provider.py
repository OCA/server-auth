# Copyright 2016 ICTSTUDIO <http://www.ictstudio.eu>
# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

import requests

from odoo import api, fields, models

try:
    from jose import jwt
except ImportError:
    logging.getLogger(__name__).debug("jose library not installed")


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    flow = fields.Selection(
        [("access_token", "OAuth2"), ("id_token", "OpenID Connect (implicit flow")],
        string="Auth Flow",
        required=True,
        default="access_token",
    )

    token_map = fields.Char(
        help="Some Oauth providers don't map keys in their responses "
        "exactly as required.  It is important to ensure user_id and "
        "email at least are mapped. For OpenID Connect user_id is "
        "the sub key in the standard."
    )

    validation_endpoint = fields.Char(
        help="For OpenID Connect this should be the location for public keys "
    )

    @api.model
    def _get_key(self, header):
        if self.flow != "id_token":
            return False
        r = requests.get(self.validation_endpoint)
        r.raise_for_status()
        response = r.json()
        rsa_key = {}
        for key in response["keys"]:
            if key["kid"] == header.get("kid"):
                rsa_key = key
        return rsa_key

    @api.model
    def _map_token_values(self, res):
        if self.token_map:
            for pair in self.token_map.split(" "):
                from_key, to_key = pair.split(":")
                if to_key not in res:
                    res[to_key] = res.get(from_key, "")
        return res

    def _parse_id_token(self, id_token, access_token):
        self.ensure_one()
        res = {}
        header = jwt.get_unverified_header(id_token)
        res.update(
            jwt.decode(
                id_token,
                self._get_key(header),
                algorithms=["RS256"],
                audience=self.client_id,
                access_token=access_token,
            )
        )

        res.update(self._map_token_values(res))
        return res
