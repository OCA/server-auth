# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

import lasso

from odoo import api, fields, models


class AuthSamlProvider(models.Model):
    """Configuration values of a SAML2 provider"""
    _name = 'auth.saml.provider'
    _description = 'SAML2 provider'
    _order = 'sequence, name'

    # Name of the OAuth2 entity, authentic, xcg...
    name = fields.Char('Provider name', required=True, index=True)
    idp_metadata = fields.Text(
        string='IDP Configuration',
        help="Configuration for this Identity Provider",
    )
    sp_metadata = fields.Text(
        string='SP Configuration',
        help="Configuration for the Service Provider (this Odoo instance)",
    )
    sp_pkey = fields.Text(
        string='SP private key',
        help="Private key for the Service Provider (this Odoo instance)",
    )
    matching_attribute = fields.Char(
        default='subject.nameId',
        required=True,
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(index=True)
    css_class = fields.Char(
        string="CSS class",
        help="Add a CSS class that serves you to style the login button.",
    )
    body = fields.Char()

    @api.multi
    def _get_lasso_for_provider(self):
        """internal helper to get a configured lasso.Login object for the
        given provider id"""

        # TODO: we should cache those results somewhere because it is
        # really costly to always recreate a login variable from buffers
        server = lasso.Server.newFromBuffers(
            self.sp_metadata,
            self.sp_pkey
        )
        server.addProviderFromBuffer(
            lasso.PROVIDER_ROLE_IDP,
            self.idp_metadata
        )
        return lasso.Login(server)

    @api.multi
    def _get_auth_request(self, state):
        """build an authentication request and give it back to our client
        """

        self.ensure_one()

        login = self._get_lasso_for_provider()

        # This part MUST be performed on each call and cannot be cached
        login.initAuthnRequest()
        login.request.nameIdPolicy.format = None
        login.request.nameIdPolicy.allowCreate = True
        login.msgRelayState = json.dumps(state)
        login.buildAuthnRequestMsg()

        # msgUrl is a fully encoded url ready for redirect use
        # obtained after the buildAuthnRequestMsg() call
        return login.msgUrl
