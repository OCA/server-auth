# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import contextlib
import time
from unittest.mock import Mock

import jwt

import odoo.http
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from ..exceptions import (
    AmbiguousJwtValidator,
    JwtValidatorNotFound,
    UnauthorizedInvalidToken,
    UnauthorizedMalformedAuthorizationHeader,
    UnauthorizedMissingAuthorizationHeader,
    UnauthorizedPartnerNotFound,
)


# Taken from odoo.tools.misc of odoo 14.0
class DotDict(dict):
    """Helper for dot.notation access to dictionary attributes
        E.g.
          foo = DotDict({'bar': False})
          return foo.bar
    """
    def __getattr__(self, attrib):
        val = self.get(attrib)
        return DotDict(val) if type(val) is dict else val


class TestAuthMethod(TransactionCase):
    @contextlib.contextmanager
    def _mock_request(self, authorization):
        request = Mock(
            context={},
            db=self.env.cr.dbname,
            uid=None,
            httprequest=Mock(environ={"HTTP_AUTHORIZATION": authorization}),
            session=DotDict(),
        )

        with contextlib.ExitStack() as s:
            odoo.http._request_stack.push(request)
            s.callback(odoo.http._request_stack.pop)
            yield request

    def _create_token(
        self,
        key="thesecret",
        audience="me",
        issuer="http://the.issuer",
        exp_delta=100,
        nbf=None,
        email=None,
    ):
        payload = dict(aud=audience, iss=issuer, exp=time.time() + exp_delta)
        if email:
            payload["email"] = email
        if nbf:
            payload["nbf"] = nbf
        return jwt.encode(payload, key=key, algorithm="HS256").decode()

    def _create_validator(self, name, audience="me", partner_id_required=False):
        return self.env["auth.jwt.validator"].create(
            dict(
                name=name,
                signature_type="secret",
                secret_algorithm="HS256",
                secret_key="thesecret",
                audience=audience,
                issuer="http://the.issuer",
                user_id_strategy="static",
                partner_id_strategy="email",
                partner_id_required=partner_id_required,
            )
        )

    @contextlib.contextmanager
    def _commit_validator(self, name, audience="me", partner_id_required=False):
        validator = self._create_validator(
            name=name, audience=audience, partner_id_required=partner_id_required
        )

        def _mocked_get_validator_by_name(self, validator_name):
            if validator_name == name:
                return validator
            return self.env["auth.jwt.validator"]._get_validator_by_name.origin(
                self, validator_name
            )

        try:
            # Patch _get_validator_by_name because IrHttp._auth_method_jwt
            # will look for the validator in another transaction,
            # where the validator we created above would not be visible.
            self.env["auth.jwt.validator"]._patch_method(
                "_get_validator_by_name", _mocked_get_validator_by_name
            )
            yield validator
        finally:
            self.env["auth.jwt.validator"]._revert_method("_get_validator_by_name")

    def test_missing_authorization_header(self):
        with self._mock_request(authorization=None):
            with self.assertRaises(UnauthorizedMissingAuthorizationHeader):
                self.env["ir.http"]._auth_method_jwt()

    def test_malformed_authorization_header(self):
        for authorization in (
            "a",
            "Bearer",
            "Bearer ",
            "Bearer x y",
            "Bearer token ",
            "bearer token",
        ):
            with self._mock_request(authorization=authorization):
                with self.assertRaises(UnauthorizedMalformedAuthorizationHeader):
                    self.env["ir.http"]._auth_method_jwt()

    def test_auth_method_valid_token(self):
        with self._commit_validator("validator"):
            authorization = "Bearer " + self._create_token()
            with self._mock_request(authorization=authorization):
                self.env["ir.http"]._auth_method_jwt_validator()

    def test_auth_method_valid_token_two_validators(self):
        with self._commit_validator(
            "validator2", audience="bad"
        ), self._commit_validator("validator3"):
            authorization = "Bearer " + self._create_token()
            with self._mock_request(authorization=authorization):
                # first validator rejects the token because of invalid audience
                with self.assertRaises(UnauthorizedInvalidToken):
                    self.env["ir.http"]._auth_method_jwt_validator2()
                # second validator accepts the token
                self.env["ir.http"]._auth_method_jwt_validator3()

    def test_auth_method_invalid_token(self):
        # Test invalid token via _auth_method_jwt
        # Other types of invalid tokens are unit tested elswhere.
        with self._commit_validator("validator4"):
            authorization = "Bearer " + self._create_token(audience="bad")
            with self._mock_request(authorization=authorization):
                with self.assertRaises(UnauthorizedInvalidToken):
                    self.env["ir.http"]._auth_method_jwt_validator4()

    def test_user_id_strategy(self):
        with self._commit_validator("validator5") as validator:
            authorization = "Bearer " + self._create_token()
            with self._mock_request(authorization=authorization) as request:
                self.env["ir.http"]._auth_method_jwt_validator5()
                self.assertEqual(request.uid, validator.static_user_id.id)

    def test_partner_id_strategy_email_found(self):
        partner = self.env["res.partner"].search([("email", "!=", False)])[0]
        with self._commit_validator("validator6"):
            authorization = "Bearer " + self._create_token(email=partner.email)
            with self._mock_request(authorization=authorization) as request:
                self.env["ir.http"]._auth_method_jwt_validator6()
                self.assertEqual(request.jwt_partner_id, partner.id)

    def test_partner_id_strategy_email_not_found(self):
        with self._commit_validator("validator6"):
            authorization = "Bearer " + self._create_token(
                email="notanemail@example.com"
            )
            with self._mock_request(authorization=authorization) as request:
                self.env["ir.http"]._auth_method_jwt_validator6()
                self.assertFalse(request.jwt_partner_id)

    def test_partner_id_strategy_email_not_found_partner_required(self):
        with self._commit_validator("validator6", partner_id_required=True):
            authorization = "Bearer " + self._create_token(
                email="notanemail@example.com"
            )
            with self._mock_request(authorization=authorization):
                with self.assertRaises(UnauthorizedPartnerNotFound):
                    self.env["ir.http"]._auth_method_jwt_validator6()

    def test_get_validator(self):
        AuthJwtValidator = self.env["auth.jwt.validator"]
        AuthJwtValidator.search([]).unlink()
        with self.assertRaises(JwtValidatorNotFound), mute_logger(
            "odoo.addons.auth_jwt.models.auth_jwt_validator"
        ):
            AuthJwtValidator._get_validator_by_name(None)
        with self.assertRaises(JwtValidatorNotFound), mute_logger(
            "odoo.addons.auth_jwt.models.auth_jwt_validator"
        ):
            AuthJwtValidator._get_validator_by_name("notavalidator")
        validator1 = self._create_validator(name="validator1")
        with self.assertRaises(JwtValidatorNotFound), mute_logger(
            "odoo.addons.auth_jwt.models.auth_jwt_validator"
        ):
            AuthJwtValidator._get_validator_by_name("notavalidator")
        self.assertEqual(AuthJwtValidator._get_validator_by_name(None), validator1)
        self.assertEqual(
            AuthJwtValidator._get_validator_by_name("validator1"), validator1
        )
        # create a second validator
        validator2 = self._create_validator(name="validator2")
        with self.assertRaises(AmbiguousJwtValidator), mute_logger(
            "odoo.addons.auth_jwt.models.auth_jwt_validator"
        ):
            AuthJwtValidator._get_validator_by_name(None)
        self.assertEqual(
            AuthJwtValidator._get_validator_by_name("validator2"), validator2
        )

    def test_bad_tokens(self):
        validator = self._create_validator("validator")
        token = self._create_token(key="badsecret")
        with self.assertRaises(UnauthorizedInvalidToken):
            validator._decode(token)
        token = self._create_token(audience="badaudience")
        with self.assertRaises(UnauthorizedInvalidToken):
            validator._decode(token)
        token = self._create_token(issuer="badissuer")
        with self.assertRaises(UnauthorizedInvalidToken):
            validator._decode(token)
        token = self._create_token(exp_delta=-100)
        with self.assertRaises(UnauthorizedInvalidToken):
            validator._decode(token)

    def test_multiple_aud(self):
        validator = self._create_validator("validator", audience="a1,a2")
        token = self._create_token(audience="a1")
        validator._decode(token)
        token = self._create_token(audience="a2")
        validator._decode(token)
        token = self._create_token(audience="a3")
        with self.assertRaises(UnauthorizedInvalidToken):
            validator._decode(token)

    def test_nbf(self):
        validator = self._create_validator("validator")
        token = self._create_token(nbf=time.time() - 60)
        validator._decode(token)
        token = self._create_token(nbf=time.time() + 60)
        with self.assertRaises(UnauthorizedInvalidToken):
            validator._decode(token)

    def test_auth_method_registration_on_create(self):
        IrHttp = self.env["ir.http"]
        self.assertFalse(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))
        self._create_validator("validator1")
        self.assertTrue(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))

    def test_auth_method_unregistration_on_unlink(self):
        IrHttp = self.env["ir.http"]
        validator = self._create_validator("validator1")
        self.assertTrue(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))
        validator.unlink()
        self.assertFalse(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))

    def test_auth_method_registration_on_rename(self):
        IrHttp = self.env["ir.http"]
        validator = self._create_validator("validator1")
        self.assertTrue(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))
        validator.name = "validator2"
        self.assertFalse(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))
        self.assertTrue(hasattr(IrHttp.__class__, "_auth_method_jwt_validator2"))

    def test_name_check(self):
        with self.assertRaises(ValidationError):
            self._create_validator(name="not an identifier")
