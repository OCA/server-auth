# Copyright 2016 ICTSTUDIO <http://www.ictstudio.eu>
# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import uuid

import werkzeug.utils

from odoo.addons.auth_oauth.controllers.main import OAuthLogin


class OpenIDLogin(OAuthLogin):
    def list_providers(self):
        providers = super(OpenIDLogin, self).list_providers()
        for provider in providers:
            if provider.get("flow") == "id_token":
                provider["nonce"] = uuid.uuid1().hex  # TODO Better nonce
                params = werkzeug.url_decode(provider["auth_link"].split("?")[-1])
                params.pop("response_type")
                params.update(
                    dict(response_type="id_token token", nonce=provider["nonce"])
                )
                if provider.get("scope"):
                    params["scope"] = provider["scope"]
                provider["auth_link"] = "{}?{}".format(
                    provider["auth_endpoint"], werkzeug.url_encode(params)
                )
        return providers
