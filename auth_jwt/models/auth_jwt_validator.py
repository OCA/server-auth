# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from functools import partial


from werkzeug.exceptions import InternalServerError

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

from ..exceptions import (
    AmbiguousJwtValidator,
    JwtValidatorNotFound,
    UnauthorizedInvalidToken,
    UnauthorizedPartnerNotFound,
)

_logger = logging.getLogger(__name__)

try:
    import jwt
except (ImportError, IOError) as err:
    _logger.debug(err)

try:
    from jwt import PyJWKClient
except (ImportError, IOError) as err:
    PyJWKClient = None
    _logger.debug(err)


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
        if not PyJWKClient:
            raise NotImplementedError("PyJWK isn't supported")

        jwks_client = PyJWKClient(self.public_key_jwk_uri, cache_keys=False)
        return jwks_client.get_signing_key(kid).key

    def _decode(self, token):
        """Validate and decode a JWT token, return the payload."""
        if self.signature_type == "secret":
            key = self.secret_key
            algorithm = self.secret_algorithm
        else:
            try:
                header = jwt.get_unverified_header(token)
            except Exception as e:
                _logger.info("Invalid token: %s", e)
                raise UnauthorizedInvalidToken()
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
            raise UnauthorizedInvalidToken()
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
                "_auth_method_jwt_{rec.name}".format(rec=rec),
                partial(IrHttp.__class__._auth_method_jwt, validator_name=rec.name),
            )

    def _unregister_auth_method(self):
        IrHttp = self.env["ir.http"]
        for rec in self:
            try:
                delattr(
                    IrHttp.__class__,
                    "_auth_method_jwt_{rec.name}".format(rec=rec)
                )
            except AttributeError:
                pass

    # model_create_multi cannot be used in 11.0
    # @api.model_create_multi
    @api.model
    def create(self, vals):
        rec = super(AuthJwtValidator, self).create(vals)
        rec._register_auth_method()
        return rec

    def write(self, vals):
        if "name" in vals:
            self._unregister_auth_method()
        res = super(AuthJwtValidator, self).write(vals)
        self._register_auth_method()
        return res

    def unlink(self):
        self._unregister_auth_method()
        return super(AuthJwtValidator, self).unlink()
