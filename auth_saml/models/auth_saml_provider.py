# Copyright (C) 2020 Glodo UK <https://www.glodo.uk/>
# Copyright (C) 2010-2016, 2022 XCG Consulting <https://xcg-consulting.fr/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import os
import tempfile
import urllib.parse

# dependency name is pysaml2 # pylint: disable=W7936
import saml2
import saml2.xmldsig as ds
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AuthSamlProvider(models.Model):
    """Configuration values of a SAML2 provider"""

    _name = "auth.saml.provider"
    _description = "SAML2 Provider"
    _order = "sequence, name"

    name = fields.Char("Provider Name", required=True, index="trigram")
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
        copy=True,
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
    # User creation fields
    create_user = fields.Boolean(
        default=False,
        help="Create user if not found. The login and name will defaults to the SAML "
        "user matching attribute. Use the mapping attributes to change the value "
        "used.",
    )
    create_user_template_id = fields.Many2one(
        comodel_name="res.users",
        # Template users, like base.default_user, are disabled by default so allow them
        domain="[('active', 'in', (True, False))]",
        default=lambda self: self.env.ref("base.default_user"),
        help="When creating user, this user is used as a template",
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
        sp_config = Saml2Config()
        sp_config.load(settings)
        sp_config.allow_unknown_attributes = True
        return sp_config

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
                break

        self._store_outstanding_request(reqid)

        return redirect_url

    def _validate_auth_response(self, token: str, base_url: str = None):
        """return the validation data corresponding to the access token"""
        self.ensure_one()

        client = self._get_client_for_provider(base_url)
        response = client.parse_authn_request_response(
            token,
            saml2.entity.BINDING_HTTP_POST,
            self._get_outstanding_requests_dict(),
        )
        try:
            matching_value = self._get_attribute_value(
                response, self.matching_attribute
            )
        except KeyError:
            raise KeyError(
                f"Matching attribute {self.matching_attribute} not found "
                f"in user attrs: {response.get_identity()}"
            ) from None
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

    @staticmethod
    def _get_attribute_value(response, attribute_name: str):
        """

        :raise: KeyError if attribute is not in the response
        :param response:
        :param attribute_name:
        :return: value of the attribut. if the value is an empty list, return None
                 otherwise return the first element of the list
        """
        if attribute_name == "subject.nameId":
            return response.name_id.text
        attrs = response.get_identity()
        attribute_value = attrs[attribute_name]
        if isinstance(attribute_value, list):
            attribute_value = next(iter(attribute_value), None)
        return attribute_value

    def _hook_validate_auth_response(self, response, matching_value):
        self.ensure_one()
        vals = {}

        for attribute in self.attribute_mapping_ids:
            try:
                vals[attribute.field_name] = self._get_attribute_value(
                    response, attribute.attribute_name
                )
            except KeyError:
                _logger.warning(
                    "SAML attribute '%s' found in response %s",
                    attribute.attribute_name,
                    response.get_identity(),
                )

        return {"mapped_attrs": vals}

    def _user_copy_defaults(self, validation):
        """
        Returns defaults when copying the template user.

        Can be overridden with extra information.
        :param validation: validation result
        :return: a dictionary for copying template user, empty to avoid copying
        """
        self.ensure_one()
        if not self.create_user:
            return {}
        saml_uid = validation["user_id"]
        return {
            "name": saml_uid,
            "login": saml_uid,
            "active": True,
            # if signature is not provided by mapped_attrs, it will be computed
            # due to call to compute method in calling method.
            "signature": None,
        } | validation.get("mapped_attrs", {})
