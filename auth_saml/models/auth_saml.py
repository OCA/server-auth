# Copyright (C) 2020 Glodo UK <https://www.glodo.uk/>
# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
import urllib.parse

import saml2
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AuthSamlProvider(models.Model):
    """Configuration values of a SAML2 provider"""

    _name = "auth.saml.provider"
    _description = "SAML2 provider"
    _order = "sequence, name"

    name = fields.Char("Provider name", required=True, index=True)

    entity_id = fields.Char(
        "Entity ID",
        help=("EntityID passed to IDP, used to identify the Odoo"),
        required=True,
        default="odoo",
    )

    idp_metadata = fields.Text(
        string="Identity Provider Metadata",
        help=(
            "Configuration for this Identity Provider. Supplied by the"
            " provider, in XML format."
        ),
    )

    sp_baseurl = fields.Text(
        string="Override Base Url",
        help="""Base Url sent to Odoo with this, rather than automatically
        detecting from request or system parameter web.base.url
        """,
    )

    sp_pem = fields.Binary(
        string="Odoo Certificate",
        help="Combined certificate and private key used by Odoo to sign",
        attachment=True,
    )

    sp_metadata_url = fields.Char(
        compute="_compute_sp_metadata_url", string="Metadata URL", readonly=True,
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
        help="""Force matching_attribute to lower case before passing back to
        Odoo.""",
    )

    attribute_mapping_ids = fields.One2many(
        "auth.saml.attribute.mapping", "provider_id", string="Attribute Mapping",
    )

    active = fields.Boolean(default=True)

    idp_allow_unsolicited = fields.Boolean(default=False)

    sequence = fields.Integer(index=True)

    css_class = fields.Char(
        string="Button Icon CSS class",
        help="Add a CSS class that serves you to style the login button.",
    )

    body = fields.Char(string="Button Description")

    @api.onchange("name")
    def _onchange(self):
        for record in self:
            if record.body:
                continue

            record.body = record.name

    @api.depends("sp_baseurl")
    def _compute_sp_metadata_url(self):
        icp_base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        )

        for record in self:
            if isinstance(record.id, models.NewId):
                record.sp_metadata_url = None
                continue

            if record.sp_baseurl:
                base_url = self.sp_baseurl
            else:
                base_url = icp_base_url

            qs = urllib.parse.urlencode({"p": record.id, "d": self.env.cr.dbname})

            record.sp_metadata_url = urllib.parse.urljoin(
                base_url, ("/auth_saml/metadata?%s" % (qs))
            )

    def _get_config_for_provider(self, base_url=None):
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

        keys = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_field", "=", "sp_pem"),
                ("res_id", "=", self.id),
            ],
            limit=1,
        )

        keys_path = self.env["ir.attachment"]._full_path(keys.store_fname)

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
                    "allow_unsolicited": self.idp_allow_unsolicited,
                    "authn_requests_signed": True,
                    "logout_requests_signed": True,
                    "want_assertions_signed": True,
                    "want_response_signed": True,
                },
            },
            "cert_file": keys_path,
            "key_file": keys_path,
        }
        spConfig = Saml2Config()
        spConfig.load(settings)
        spConfig.allow_unknown_attributes = True
        return spConfig

    def _get_client_for_provider(self, base_url=None):
        spConfig = self._get_config_for_provider(base_url)
        saml_client = Saml2Client(config=spConfig)
        return saml_client

    def _get_auth_request(self, extra_state=None):
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

        saml_client = self._get_client_for_provider()
        reqid, info = saml_client.prepare_for_authenticate(
            relay_state=json.dumps(state)
        )

        redirect_url = None
        # Select the IdP URL to send the AuthN request to
        for key, value in info["headers"]:
            if key == "Location":
                redirect_url = value

        self._store_outstanding_request(reqid)

        return redirect_url

    def _validate_auth_response(self, token):
        """ return the validation data corresponding to the access token """
        self.ensure_one()

        client = self._get_client_for_provider()

        response = client.parse_authn_request_response(
            token,
            saml2.entity.BINDING_HTTP_POST,
            self._get_outstanding_requests_dict(),
        )

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

        if not self.idp_allow_unsolicited:
            self.env["auth_saml.request"].sudo().create(
                {"saml_provider_id": self.id, "saml_request_id": reqid}
            )

    def _metadata_string(self, valid=None, signed=False):
        self.ensure_one()

        keys = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_field", "=", "sp_pem"),
                ("res_id", "=", self.id),
            ],
            limit=1,
        )

        keys_path = self.env["ir.attachment"]._full_path(keys.store_fname)

        sp_config = self._get_config_for_provider()
        return saml2.metadata.create_metadata_string(
            None,
            config=sp_config,
            valid=valid,
            cert=keys_path,
            keyfile=keys_path,
            sign=signed,
        )

    def _hook_validate_auth_response(self, response, matching_value):
        self.ensure_one()
        vals = {}
        attrs = response.get_identity()

        for attribute in self.attribute_mapping_ids:
            if attribute.attribute_name not in attrs:
                _logger.info(
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
