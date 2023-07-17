# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
import logging
import re
from calendar import timegm
from functools import partial

import jwt  # pylint: disable=missing-manifest-dependency
from jwt import PyJWKClient
from werkzeug.exceptions import InternalServerError

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

from ..exceptions import (
    AmbiguousJwtValidator,
    ConfigurationError,
    JwtValidatorNotFound,
    UnauthorizedInvalidToken,
    UnauthorizedMalformedAuthorizationHeader,
    UnauthorizedMissingAuthorizationHeader,
    UnauthorizedPartnerNotFound,
)

_logger = logging.getLogger(__name__)

AUTHORIZATION_RE = re.compile(r"^Bearer ([^ ]+)$")


class AuthJwtValidator(models.Model):
    _name = "auth.jwt.validator"
    _description = "JWT Validator Configuration"

    name = fields.Char(required=True)
    signature_type = fields.Selection(
        [("secret", "Secret"), ("public_key", "Public key")], required=True
    )
    secret_key = fields.Char()
    secret_algorithm = fields.Selection(
        [
            # https://pyjwt.readthedocs.io/en/stable/algorithms.html
            ("HS256", "HS256 - HMAC using SHA-256 hash algorithm"),
            ("HS384", "HS384 - HMAC using SHA-384 hash algorithm"),
            ("HS512", "HS512 - HMAC using SHA-512 hash algorithm"),
        ],
        default="HS256",
    )
    public_key_jwk_uri = fields.Char()
    public_key_algorithm = fields.Selection(
        [
            # https://pyjwt.readthedocs.io/en/stable/algorithms.html
            ("ES256", "ES256 - ECDSA using SHA-256"),
            ("ES256K", "ES256K - ECDSA with secp256k1 curve using SHA-256"),
            ("ES384", "ES384 - ECDSA using SHA-384"),
            ("ES512", "ES512 - ECDSA using SHA-512"),
            ("RS256", "RS256 - RSASSA-PKCS1-v1_5 using SHA-256"),
            ("RS384", "RS384 - RSASSA-PKCS1-v1_5 using SHA-384"),
            ("RS512", "RS512 - RSASSA-PKCS1-v1_5 using SHA-512"),
            ("PS256", "PS256 - RSASSA-PSS using SHA-256 and MGF1 padding with SHA-256"),
            ("PS384", "PS384 - RSASSA-PSS using SHA-384 and MGF1 padding with SHA-384"),
            ("PS512", "PS512 - RSASSA-PSS using SHA-512 and MGF1 padding with SHA-512"),
        ],
        default="RS256",
    )
    audience = fields.Char(
        required=True, help="Comma separated list of audiences, to validate aud."
    )
    issuer = fields.Char(required=True, help="To validate iss.")
    user_id_strategy = fields.Selection(
        [("static", "Static")], required=True, default="static"
    )
    static_user_id = fields.Many2one("res.users", default=1)
    partner_id_strategy = fields.Selection([("email", "From email claim")])
    partner_id_required = fields.Boolean()

    next_validator_id = fields.Many2one(
        "auth.jwt.validator",
        domain="[('id', '!=', id)]",
        help="Next validator to try if this one fails",
    )

    cookie_enabled = fields.Boolean(
        help=(
            "Convert the JWT token into an HttpOnly Secure cookie. "
            "When both an Authorization header and the cookie are present "
            "in the request, the cookie is ignored."
        )
    )
    cookie_name = fields.Char(default="authorization")
    cookie_path = fields.Char(default="/")
    cookie_max_age = fields.Integer(
        default=86400 * 365,
        help="Number of seconds until the cookie expires (Max-Age).",
    )
    cookie_secure = fields.Boolean(
        default=True, help="Set to false only for development without https."
    )

    _sql_constraints = [
        ("name_uniq", "unique(name)", "JWT validator names must be unique !"),
    ]

    @api.constrains("name")
    def _check_name(self):
        for rec in self:
            if not rec.name.isidentifier():
                raise ValidationError(
                    _("Name %r is not a valid python identifier.") % (rec.name,)
                )

    @api.constrains("next_validator_id")
    def _check_next_validator_id(self):
        # Prevent circular references
        for rec in self:
            validator = rec
            chain = [validator.name]
            while validator:
                validator = validator.next_validator_id
                chain.append(validator.name)
                if rec == validator:
                    raise ValidationError(
                        _("Validators mustn't make a closed chain: {}.").format(
                            " -> ".join(chain)
                        )
                    )

    @api.constrains("cookie_enabled", "cookie_name")
    def _check_cookie_name(self):
        for rec in self:
            if rec.cookie_enabled and not rec.cookie_name:
                raise ValidationError(
                    _(
                        "A cookie name must be provided on JWT validator %s "
                        "because it has cookie mode enabled."
                    )
                    % (rec.name,)
                )

    @api.model
    def _get_validator_by_name_domain(self, validator_name):
        if validator_name:
            return [("name", "=", validator_name)]
        return []

    @api.model
    def _get_validator_by_name(self, validator_name):
        domain = self._get_validator_by_name_domain(validator_name)
        validator = self.search(domain)
        if not validator:
            _logger.error("JWT validator not found for name %r", validator_name)
            raise JwtValidatorNotFound()
        if len(validator) != 1:
            _logger.error(
                "More than one JWT validator found for name %r", validator_name
            )
            raise AmbiguousJwtValidator()
        return validator

    @tools.ormcache("self.public_key_jwk_uri", "kid")
    def _get_key(self, kid):
        jwks_client = PyJWKClient(self.public_key_jwk_uri, cache_keys=False)
        return jwks_client.get_signing_key(kid).key

    def _encode(self, payload, secret, expire):
        """Encode and sign a JWT payload so it can be decoded and validated with
        _decode().

        The aud and iss claims are set to this validator's values.
        The exp claim is set according to the expire parameter.
        """
        payload = dict(
            payload,
            exp=timegm(datetime.datetime.utcnow().utctimetuple()) + expire,
            aud=self.audience,
            iss=self.issuer,
        )
        return jwt.encode(payload, key=secret, algorithm="HS256")

    def _decode(self, token, secret=None):
        """Validate and decode a JWT token, return the payload."""
        if secret:
            key = secret
            algorithm = "HS256"
        elif self.signature_type == "secret":
            key = self.secret_key
            algorithm = self.secret_algorithm
        else:
            try:
                header = jwt.get_unverified_header(token)
            except Exception as e:
                _logger.info("Invalid token: %s", e)
                raise UnauthorizedInvalidToken() from e
            key = self._get_key(header.get("kid"))
            algorithm = self.public_key_algorithm
        try:
            payload = jwt.decode(
                token,
                key=key,
                algorithms=[algorithm],
                options=dict(
                    require=["exp", "aud", "iss"],
                    verify_exp=True,
                    verify_aud=True,
                    verify_iss=True,
                ),
                audience=self.audience.split(","),
                issuer=self.issuer,
            )
        except Exception as e:
            _logger.info("Invalid token: %s", e)
            raise UnauthorizedInvalidToken() from e
        return payload

    def _get_uid(self, payload):
        # override for additional strategies
        if self.user_id_strategy == "static":
            return self.static_user_id.id

    def _get_and_check_uid(self, payload):
        uid = self._get_uid(payload)
        if not uid:
            _logger.error("_get_uid did not return a user id")
            raise InternalServerError()
        return uid

    def _get_partner_id(self, payload):
        # override for additional strategies
        if self.partner_id_strategy == "email":
            email = payload.get("email")
            if not email:
                _logger.debug("JWT payload does not have an email claim")
                return
            partner = self.env["res.partner"].search([("email", "=", email)])
            if len(partner) != 1:
                _logger.debug("%d partners found for email %s", len(partner), email)
                return
            return partner.id

    def _get_and_check_partner_id(self, payload):
        partner_id = self._get_partner_id(payload)
        if not partner_id and self.partner_id_required:
            raise UnauthorizedPartnerNotFound()
        return partner_id

    def _register_hook(self):
        res = super()._register_hook()
        self.search([])._register_auth_method()
        return res

    def _register_auth_method(self):
        IrHttp = self.env["ir.http"]
        for rec in self:
            setattr(
                IrHttp.__class__,
                f"_auth_method_jwt_{rec.name}",
                partial(IrHttp.__class__._auth_method_jwt, validator_name=rec.name),
            )
            setattr(
                IrHttp.__class__,
                f"_auth_method_public_or_jwt_{rec.name}",
                partial(
                    IrHttp.__class__._auth_method_public_or_jwt, validator_name=rec.name
                ),
            )

    def _unregister_auth_method(self):
        IrHttp = self.env["ir.http"]
        for rec in self:
            try:
                delattr(IrHttp.__class__, f"_auth_method_jwt_{rec.name}")
                delattr(IrHttp.__class__, f"_auth_method_public_or_jwt_{rec.name}")
            except AttributeError:  # pylint: disable=except-pass
                pass

    @api.model_create_multi
    def create(self, vals):
        rec = super().create(vals)
        rec._register_auth_method()
        return rec

    def write(self, vals):
        if "name" in vals:
            self._unregister_auth_method()
        res = super().write(vals)
        self._register_auth_method()
        return res

    def unlink(self):
        self._unregister_auth_method()
        return super().unlink()

    def _get_jwt_cookie_secret(self):
        secret = self.env["ir.config_parameter"].sudo().get_param("database.secret")
        if not secret:
            _logger.error("database.secret system parameter is not set.")
            raise ConfigurationError()
        return secret

    @api.model
    def _parse_bearer_authorization(self, authorization):
        """Parse a Bearer token authorization header and return the token.

        Raises UnauthorizedMissingAuthorizationHeader if authorization is falsy.
        Raises UnauthorizedMalformedAuthorizationHeader if invalid.
        """
        if not authorization:
            _logger.info("Missing Authorization header.")
            raise UnauthorizedMissingAuthorizationHeader()
        # https://tools.ietf.org/html/rfc6750#section-2.1
        mo = AUTHORIZATION_RE.match(authorization)
        if not mo:
            _logger.info("Malformed Authorization header.")
            raise UnauthorizedMalformedAuthorizationHeader()
        return mo.group(1)
