# Copyright (C) 2020 Glodo UK <https://www.glodo.uk/>
# Copyright (C) 2010-2016, 2022 XCG Consulting <https://xcg-consulting.fr/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import os
import tempfile
import urllib.parse

import requests

# dependency name is pysaml2 # pylint: disable=W7936
import saml2
import saml2.xmldsig as ds
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
from saml2.sigver import SignatureError

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AuthSamlProvider(models.Model):
    """Configuration values of a SAML2 provider"""

    _name = "auth.saml.provider"
    _description = "SAML2 Provider"
    _order = "sequence, name"

    name = fields.Char("Provider Name", required=True, index=True)
    entity_id = fields.Char(
        "Entity ID",
        help="EntityID passed to IDP, used to identify the Odoo",
        required=True,
        default="odoo",
    )
    idp_metadata = fields.Text(
        string="Identity Provider Metadata",
        help=(
            "Configuration for this Identity Provider. Supplied by the"
            " provider, in XML format."
        ),
        required=True,
    )
    idp_metadata_url = fields.Char(
        string="Identity Provider Metadata URL",
        help="Some SAML providers, notably Office365 can have a metadata "
        "document which changes over time, and they provide a URL to the "
        "document instead. When this field is set, the metadata can be "
        "fetched from the provided URL.",
    )

    sp_baseurl = fields.Text(
        string="Override Base URL",
        help="""Base URL sent to Odoo with this, rather than automatically
        detecting from request or system parameter web.base.url""",
    )
    sp_pem_public = fields.Binary(
        string="Odoo Public Certificate",
        attachment=True,
        required=True,
    )
    sp_pem_public_filename = fields.Char("Odoo Public Certificate File Name")
    sp_pem_private = fields.Binary(
        string="Odoo Private Key",
        attachment=True,
        required=True,
    )
    sp_pem_private_filename = fields.Char("Odoo Private Key File Name")
    sp_metadata_url = fields.Char(
        compute="_compute_sp_metadata_url",
        string="Metadata URL",
        readonly=True,
    )
    matching_attribute = fields.Char(
        string="Identity Provider matching attribute",
        default="subject.nameId",
        required=True,
        help=(
            "Attribute to look for in the returned IDP response to match"
            " against an Odoo user."
        ),
    )
    matching_attribute_to_lower = fields.Boolean(
        string="Lowercase IDP Matching Attribute",
        help="Force matching_attribute to lower case before passing back to Odoo.",
    )
    attribute_mapping_ids = fields.One2many(
        "auth.saml.attribute.mapping",
        "provider_id",
        string="Attribute Mapping",
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(index=True)
    css_class = fields.Char(
        string="Button Icon CSS class",
        help="Add a CSS class that serves you to style the login button.",
        default="fa fa-fw fa-sign-in text-primary",
    )
    body = fields.Char(
        string="Login button label", help="Link text in Login Dialog", translate=True
    )
    autoredirect = fields.Boolean(
        "Automatic Redirection",
        default=False,
        help="Only the provider with the higher priority will be automatically "
        "redirected",
    )
    sig_alg = fields.Selection(
        selection=lambda s: s._sig_alg_selection(),
        required=True,
        string="Signature Algorithm",
    )
    # help string is from pysaml2 documentation
    authn_requests_signed = fields.Boolean(
        default=True,
        help="Indicates if the Authentication Requests sent by this SP should be signed"
        " by default.",
    )
    logout_requests_signed = fields.Boolean(
        default=True,
        help="Indicates if this entity will sign the Logout Requests originated from it"
        ".",
    )
    want_assertions_signed = fields.Boolean(
        default=True,
        help="Indicates if this SP wants the IdP to send the assertions signed.",
    )
    want_response_signed = fields.Boolean(
        default=True,
        help="Indicates that Authentication Responses to this SP must be signed.",
    )
    want_assertions_or_response_signed = fields.Boolean(
        default=True,
        help="Indicates that either the Authentication Response or the assertions "
        "contained within the response to this SP must be signed.",
    )
    # this one is used in Saml2Client.prepare_for_authenticate
    sign_authenticate_requests = fields.Boolean(
        default=True,
        help="Whether the request should be signed or not",
    )
    sign_metadata = fields.Boolean(
        default=True,
        help="Whether metadata should be signed or not",
    )

    @api.model
    def _sig_alg_selection(self):
        return [(sig[0], sig[0]) for sig in ds.SIG_ALLOWED_ALG]

    @api.onchange("name")
    def _onchange_name(self):
        if not self.body:
            self.body = self.name

    @api.depends("sp_baseurl")
    def _compute_sp_metadata_url(self):
        icp_base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        )

        for record in self:
            if isinstance(record.id, models.NewId):
                record.sp_metadata_url = False
                continue

            base_url = icp_base_url
            if record.sp_baseurl:
                base_url = record.sp_baseurl

            qs = urllib.parse.urlencode({"p": record.id, "d": self.env.cr.dbname})

            record.sp_metadata_url = urllib.parse.urljoin(
                base_url, ("/auth_saml/metadata?%s" % qs)
            )

    def _get_cert_key_path(self, field="sp_pem_public"):
        self.ensure_one()

        model_attachment = self.env["ir.attachment"].sudo()
        keys = model_attachment.search(
            [
                ("res_model", "=", self._name),
                ("res_field", "=", field),
                ("res_id", "=", self.id),
            ],
            limit=1,
        )

        if model_attachment._storage() != "file":
            # For non-file locations we need to create a temp file to pass to pysaml.
            fd, keys_path = tempfile.mkstemp()
            with open(keys_path, "wb") as f:
                f.write(base64.b64decode(keys.datas))
            os.close(fd)
        else:
            keys_path = model_attachment._full_path(keys.store_fname)

        return keys_path

    def _get_config_for_provider(self, base_url: str = None) -> Saml2Config:
        """
        Internal helper to get a configured Saml2Client
        """
        self.ensure_one()

        if self.sp_baseurl:
            base_url = self.sp_baseurl

        if not base_url:
            base_url = (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
            )

        acs_url = urllib.parse.urljoin(base_url, "/auth_saml/signin")
        settings = {
            "metadata": {"inline": [self.idp_metadata]},
            "entityid": self.entity_id,
            "service": {
                "sp": {
                    "endpoints": {
                        "assertion_consumer_service": [
                            (acs_url, saml2.BINDING_HTTP_REDIRECT),
                            (acs_url, saml2.BINDING_HTTP_POST),
                            (acs_url, saml2.BINDING_HTTP_REDIRECT),
                            (acs_url, saml2.BINDING_HTTP_POST),
                        ],
                    },
                    "allow_unsolicited": False,
                    "authn_requests_signed": self.authn_requests_signed,
                    "logout_requests_signed": self.logout_requests_signed,
                    "want_assertions_signed": self.want_assertions_signed,
                    "want_response_signed": self.want_response_signed,
                    "want_assertions_or_response_signed": (
                        self.want_assertions_or_response_signed
                    ),
                },
            },
            "cert_file": self._get_cert_key_path("sp_pem_public"),
            "key_file": self._get_cert_key_path("sp_pem_private"),
        }
        try:
            sp_config = Saml2Config()
            sp_config.load(settings)
            sp_config.allow_unknown_attributes = True
            return sp_config
        except saml2.SAMLError:
            if self.env.context.get("saml2_retry_after_refresh_metadata", False):
                raise
            # Retry after refresh metadata
            self.action_refresh_metadata_from_url()
            return self.with_context(
                saml2_retry_after_refresh_metatata=1
            )._get_config_for_provider(base_url)

    def _get_client_for_provider(self, base_url: str = None) -> Saml2Client:
        sp_config = self._get_config_for_provider(base_url)
        saml_client = Saml2Client(config=sp_config)
        return saml_client

    def _get_auth_request(self, extra_state=None, url_root=None):
        """
        build an authentication request and give it back to our client
        """
        self.ensure_one()

        if extra_state is None:
            extra_state = {}
        state = {
            "d": self.env.cr.dbname,
            "p": self.id,
        }
        state.update(extra_state)

        sig_alg = ds.SIG_RSA_SHA1
        if self.sig_alg:
            sig_alg = getattr(ds, self.sig_alg)

        saml_client = self._get_client_for_provider(url_root)
        reqid, info = saml_client.prepare_for_authenticate(
            sign=self.sign_authenticate_requests,
            relay_state=json.dumps(state),
            sigalg=sig_alg,
        )

        redirect_url = None
        # Select the IdP URL to send the AuthN request to
        for key, value in info["headers"]:
            if key == "Location":
                redirect_url = value

        self._store_outstanding_request(reqid)

        return redirect_url

    def _validate_auth_response(self, token: str, base_url: str = None):
        """return the validation data corresponding to the access token"""
        self.ensure_one()
        try:
            client = self._get_client_for_provider(base_url)
            response = client.parse_authn_request_response(
                token,
                saml2.entity.BINDING_HTTP_POST,
                self._get_outstanding_requests_dict(),
            )
        except SignatureError:
            # we have a metadata url: try to refresh the metadata document
            if self.idp_metadata_url:
                self.action_refresh_metadata_from_url()
                # retry: if it fails again, we let the exception flow
                client = self._get_client_for_provider(base_url)
                response = client.parse_authn_request_response(
                    token,
                    saml2.entity.BINDING_HTTP_POST,
                    self._get_outstanding_requests_dict(),
                )
            else:
                raise
        matching_value = None

        if self.matching_attribute == "subject.nameId":
            matching_value = response.name_id.text
        else:
            attrs = response.get_identity()

            for k, v in attrs.items():
                if k == self.matching_attribute:
                    matching_value = v
                    break

            if not matching_value:
                raise Exception(
                    "Matching attribute %s not found in user attrs: %s"
                    % (self.matching_attribute, attrs)
                )

        if matching_value and isinstance(matching_value, list):
            matching_value = next(iter(matching_value), None)

        if isinstance(matching_value, str) and self.matching_attribute_to_lower:
            matching_value = matching_value.lower()

        vals = {"user_id": matching_value}

        post_vals = self._hook_validate_auth_response(response, matching_value)
        if post_vals:
            vals.update(post_vals)

        return vals

    def _get_outstanding_requests_dict(self):
        self.ensure_one()

        requests = (
            self.env["auth_saml.request"]
            .sudo()
            .search([("saml_provider_id", "=", self.id)])
        )
        return {record.saml_request_id: record.id for record in requests}

    def _store_outstanding_request(self, reqid):
        self.ensure_one()

        self.env["auth_saml.request"].sudo().create(
            {"saml_provider_id": self.id, "saml_request_id": reqid}
        )

    def _metadata_string(self, valid=None, base_url: str = None):
        self.ensure_one()

        sp_config = self._get_config_for_provider(base_url)
        return saml2.metadata.create_metadata_string(
            None,
            config=sp_config,
            valid=valid,
            cert=self._get_cert_key_path("sp_pem_public"),
            keyfile=self._get_cert_key_path("sp_pem_private"),
            sign=self.sign_metadata,
        )

    def _hook_validate_auth_response(self, response, matching_value):
        self.ensure_one()
        vals = {}
        attrs = response.get_identity()

        for attribute in self.attribute_mapping_ids:
            if attribute.attribute_name not in attrs:
                _logger.debug(
                    "SAML attribute '%s' found in response %s",
                    attribute.attribute_name,
                    attrs,
                )
                continue

            attribute_value = attrs[attribute.attribute_name]
            if isinstance(attribute_value, list):
                attribute_value = attribute_value[0]

            vals[attribute.field_name] = attribute_value

        return {"mapped_attrs": vals}

    def action_refresh_metadata_from_url(self):
        providers = self.search(
            [("idp_metadata_url", "ilike", "http%"), ("id", "in", self.ids)]
        )
        if not providers:
            return False

        providers_to_update = {}
        for provider in providers:
            document = requests.get(provider.idp_metadata_url, timeout=5)
            if document.status_code != 200:
                raise UserError(
                    f"Unable to download the metadata for {provider.name}: {document.reason}"
                )
            if document.text != provider.idp_metadata:
                providers_to_update[provider.id] = document.text

        # lock the records we might update, so that multiple simultaneous login
        # attempts will not cause concurrent updates
        self.env.cr.execute(
            "SELECT id FROM auth_saml_provider WHERE id in %s FOR UPDATE",
            (tuple(providers_to_update.keys()),),
        )
        updated = False
        for provider in providers:
            if provider.id in providers_to_update:
                provider.idp_metadata = providers_to_update[provider.id]
                _logger.info(
                    "Updated metadata for provider %s from %s",
                    provider.name,
                )
                updated = True

        return updated
