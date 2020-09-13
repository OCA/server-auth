# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from urllib.parse import urlparse
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.auth import OneLogin_Saml2_Auth

from odoo import api, fields, models
from odoo.tools import safe_eval as eval
from odoo.exceptions import AccessDenied

import logging
_logger = logging.getLogger(__name__)

class AuthSamlProvider(models.Model):
    """Configuration values of a SAML2 provider"""
    _name = 'auth.saml.provider'
    _description = 'SAML2 provider'
    _order = 'sequence, name'

    # Name of the OAuth2 entity, authentic, xcg...
    name = fields.Char('Provider name', required=True, index=True)
    settings = fields.Text(
        string='SAML Settings',
        help="Settings for the SAML connection. See the OneLogin_Saml2_Settings class of Onelogin's SAML module (https://github.com/onelogin/python3-saml)",
        default="""{
    "strict": True,
    "debug": True,
    "security": {'authnRequestsSigned': True},
}"""
    )
    idp_metadata = fields.Text(
        string='IDP Configuration',
        help="Configuration for this Identity Provider",
        default="""{
    "entityId": "",
    "singleSignOnService": {
        "url": "",
        "binding": ""
    },
    "singleLogoutService": {
        "url": "",
        "binding": ""
    },
    "x509cert": ""
}"""
    )
    sp_metadata = fields.Text(
        string='SP Configuration',
        help="Configuration for the Service Provider (this Odoo instance)",
        default=lambda self: self._default_sp_metadata(),
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
    debug = fields.Boolean(string='Debug', default=True)
    sequence = fields.Integer(index=True)
    css_class = fields.Char(
        string="CSS class",
        help="Add a CSS class that serves you to style the login button.",
    )
    body = fields.Char()
    lowercase_urlencoding = fields.Boolean(
        string='Lowercase URL-encoding',
        help="Needed for some IDPs, such as ADFS.",
        default=False,
    )



    @api.model
    def _default_sp_metadata(self):
        template = """{{
    "entityId": "{base_url}/metadata",
    "assertionConsumerService": {{
        "url": "{base_url}/auth_saml/signin",
        "binding": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    }},
    
    "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
    "x509cert": "",
}}"""
        #"singleLogoutService": {
        #    "url": "{base_url}/auth_saml/signout",
        #    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        #},
        return template.format(base_url=self.env['ir.config_parameter'].get_param('web.base.url'))

    @api.multi
    def _get_settings_for_provider(self):
        if self.settings:
            settings = eval(self.settings)
        else:
            settings = {
                'strict': True,
                'security': {'authnRequestsSigned': True},
            }
        settings.update({
            'debug': self.debug,
            'sp': eval(self.sp_metadata),
            'idp': eval(self.idp_metadata),
        })
        settings['sp']['privateKey'] = self.sp_pkey
        return OneLogin_Saml2_Settings(settings)

    @api.multi
    def _prepare_onelogin_request(self, request, post=None):
        """ Prepare request description for OneLogin_Saml2_Auth.
            :param request: The Odoo request object.
        """
        post = post or {}
        # Use the external URL in case we're behind a proxy.
        url_data = urlparse(self.env['ir.config_parameter'].get_param('web.base.url'))
        if ':' in url_data.netloc:
            host, port = url_data.netloc.split(':')
        else:
            host = url_data.netloc
            port = None
        return {
            'https': 'on' if url_data.scheme == 'https' else 'off',
            'http_host': host,
            'server_port': port,
            'script_name': '/auth_saml/signin',
            'get_data': {},
            'lowercase_urlencoding': self.lowercase_urlencoding,
            'post_data': post.copy(),
        }
    
    @api.multi
    def _get_onelogin_server(self, request=None, post=None):
        self.ensure_one()
        settings = self._get_settings_for_provider()
        # req is used to build return URL (sent as RelayState), or provide response data.
        req = request and self._prepare_onelogin_request(request, post)
        return OneLogin_Saml2_Auth(req, settings)
    
    @api.multi
    def _get_auth_request(self, state):
        """build an authentication request and give it back to our client
        """
        self.ensure_one()
        server = self._get_onelogin_server()
        # return_to is sent as RelayState. Certain providers insist on using it as the return URL
        # even though it's not supported by the standard. We just want our state returned to us.
        return server.login(return_to=json.dumps(state)), server.get_last_request_id()
    
    @api.multi
    def authenticate(self, request, post):
        server = self._get_onelogin_server(request, post)
        request_id = request.session.get('saml_request_id')
        server.process_response(request_id=request_id)
        errors = server.get_errors()
        if not server.is_authenticated():
            _logger.debug("SAML authentication invalid.")
            raise AccessDenied("SAML authentication invalid.")
        if len(errors) == 0:
            if 'saml_request_id' in request.session:
                del request.session['saml_request_id']
            user = self.get_saml_user(server)
            if not user:
                _logger.debug('No user found for SAML request')
                raise AccessDenied('No user found for SAML request')
            return user.get_saml_data(server)
        _logger.debug("SAML errors: %s" % ', '.join(errors))
        raise AccessDenied("SAML errors.")
    
    @api.multi
    def get_saml_user(self, server):
        if self.matching_attribute == 'subject.nameId':
            uid = server.get_nameid()
        else:
            uid = server.get_attribute(self.matching_attribute)
        return self.env['res.users'].search([('saml_provider_id', '=', self.id), ('saml_uid', '=', uid)])

