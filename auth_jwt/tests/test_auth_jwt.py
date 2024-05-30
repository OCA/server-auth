# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import contextlib
import time
from unittest.mock import Mock

import jwt

import odoo.http
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger
from odoo.tools.misc import DotDict

from ..exceptions import (
    AmbiguousJwtValidator,
    JwtValidatorNotFound,
    UnauthorizedCompositeJwtError,
    UnauthorizedInvalidToken,
    UnauthorizedMalformedAuthorizationHeader,
    UnauthorizedMissingAuthorizationHeader,
    UnauthorizedPartnerNotFound,
)


class TestAuthMethod(TransactionCase):
    @contextlib.contextmanager
    def _mock_request(self, authorization):
        environ = {}
        if authorization:
            environ["HTTP_AUTHORIZATION"] = authorization
        request = Mock(
            context={},
            db=self.env.cr.dbname,
            uid=None,
            httprequest=Mock(environ=environ),
            session=DotDict(),
            env=self.env,
            cr=self.env.cr,
        )
        # These attributes are added upon successful auth, so make sure
        # calling hasattr on the mock when they are not yet set returns False.
        del request.jwt_payload
        del request.jwt_partner_id

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
        return jwt.encode(payload, key=key, algorithm="HS256")

    def _create_validator(
        self,
        name,
        audience="me",
        issuer="http://the.issuer",
        secret_key="thesecret",
        partner_id_required=False,
        static_user_id=1,
    ):
        return self.env["auth.jwt.validator"].create(
            dict(
                name=name,
                signature_type="secret",
                secret_algorithm="HS256",
                secret_key=secret_key,
                audience=audience,
                issuer=issuer,
                user_id_strategy="static",
                static_user_id=static_user_id,
                partner_id_strategy="email",
                partner_id_required=partner_id_required,
            )
        )

    def test_missing_authorization_header(self):
        self._create_validator("validator")
        with self._mock_request(authorization=None):
            with self.assertRaises(UnauthorizedMissingAuthorizationHeader):
                self.env["ir.http"]._auth_method_jwt(validator_name="validator")

    def test_malformed_authorization_header(self):
        self._create_validator("validator")
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
                    self.env["ir.http"]._auth_method_jwt(validator_name="validator")

    def test_auth_method_valid_token(self):
        self._create_validator("validator")
        authorization = "Bearer " + self._create_token()
        with self._mock_request(authorization=authorization):
            self.env["ir.http"]._auth_method_jwt_validator()

    def test_auth_method_valid_token_two_validators_one_bad_issuer(self):
        self._create_validator("validator2", issuer="http://other.issuer")
        self._create_validator("validator3")

        authorization = "Bearer " + self._create_token()
        with self._mock_request(authorization=authorization):
            # first validator rejects the token because of invalid audience
            with self.assertRaises(UnauthorizedInvalidToken):
                self.env["ir.http"]._auth_method_jwt_validator2()
            # second validator accepts the token
            self.env["ir.http"]._auth_method_jwt_validator3()

    def test_auth_method_valid_token_two_validators_one_bad_issuer_chained(self):
        validator2 = self._create_validator("validator2", issuer="http://other.issuer")
        validator3 = self._create_validator("validator3")
        validator2.next_validator_id = validator3

        authorization = "Bearer " + self._create_token()
        with self._mock_request(authorization=authorization):
            # Validator2 rejects the token because of invalid issuer but chain
            # on validator3 which accepts it
            self.env["ir.http"]._auth_method_jwt_validator2()

    def test_auth_method_valid_token_two_validators_one_bad_audience(self):
        self._create_validator("validator2", audience="bad")
        self._create_validator("validator3")

        authorization = "Bearer " + self._create_token()
        with self._mock_request(authorization=authorization):
            # first validator rejects the token because of invalid audience
            with self.assertRaises(UnauthorizedInvalidToken):
                self.env["ir.http"]._auth_method_jwt_validator2()
            # second validator accepts the token
            self.env["ir.http"]._auth_method_jwt_validator3()

    def test_auth_method_valid_token_two_validators_one_bad_audience_chained(self):
        validator2 = self._create_validator("validator2", audience="bad")
        validator3 = self._create_validator("validator3")

        validator2.next_validator_id = validator3
        authorization = "Bearer " + self._create_token()
        with self._mock_request(authorization=authorization):
            self.env["ir.http"]._auth_method_jwt_validator2()

    def test_auth_method_invalid_token(self):
        # Test invalid token via _auth_method_jwt
        # Other types of invalid tokens are unit tested elswhere.
        self._create_validator("validator4")
        authorization = "Bearer " + self._create_token(audience="bad")
        with self._mock_request(authorization=authorization):
            with self.assertRaises(UnauthorizedInvalidToken):
                self.env["ir.http"]._auth_method_jwt_validator4()

    def test_auth_method_invalid_token_on_chain(self):
        validator1 = self._create_validator("validator", issuer="http://other.issuer")
        validator2 = self._create_validator("validator2", audience="bad audience")
        validator3 = self._create_validator("validator3", secret_key="bad key")
        validator4 = self._create_validator(
            "validator4", issuer="http://other.issuer", audience="bad audience"
        )
        validator5 = self._create_validator(
            "validator5", issuer="http://other.issuer", secret_key="bad key"
        )
        validator6 = self._create_validator(
            "validator6", audience="bad audience", secret_key="bad key"
        )
        validator7 = self._create_validator(
            "validator7",
            issuer="http://other.issuer",
            audience="bad audience",
            secret_key="bad key",
        )
        validator1.next_validator_id = validator2
        validator2.next_validator_id = validator3
        validator3.next_validator_id = validator4
        validator4.next_validator_id = validator5
        validator5.next_validator_id = validator6
        validator6.next_validator_id = validator7

        authorization = "Bearer " + self._create_token()
        with self._mock_request(authorization=authorization):
            with self.assertRaises(UnauthorizedCompositeJwtError) as composite_error:
                self.env["ir.http"]._auth_method_jwt_validator()
            self.assertEqual(
                str(composite_error.exception),
                "401 Unauthorized: "
                "Multiple errors occurred during JWT chain validation:\n"
                "validator: 401 Unauthorized: "
                "The server could not verify that you are authorized to "
                "access the URL requested. You either supplied the wrong "
                "credentials (e.g. a bad password), or your browser doesn't "
                "understand how to supply the credentials required.\n"
                "validator2: 401 Unauthorized: "
                "The server could not verify that you are authorized to "
                "access the URL requested. You either supplied the wrong "
                "credentials (e.g. a bad password), or your browser doesn't "
                "understand how to supply the credentials required.\n"
                "validator3: 401 Unauthorized: "
                "The server could not verify that you are authorized to "
                "access the URL requested. You either supplied the wrong "
                "credentials (e.g. a bad password), or your browser doesn't "
                "understand how to supply the credentials required.\n"
                "validator4: 401 Unauthorized: "
                "The server could not verify that you are authorized to "
                "access the URL requested. You either supplied the wrong "
                "credentials (e.g. a bad password), or your browser doesn't "
                "understand how to supply the credentials required.\n"
                "validator5: 401 Unauthorized: "
                "The server could not verify that you are authorized to "
                "access the URL requested. You either supplied the wrong "
                "credentials (e.g. a bad password), or your browser doesn't "
                "understand how to supply the credentials required.\n"
                "validator6: 401 Unauthorized: "
                "The server could not verify that you are authorized to "
                "access the URL requested. You either supplied the wrong "
                "credentials (e.g. a bad password), or your browser doesn't "
                "understand how to supply the credentials required.\n"
                "validator7: 401 Unauthorized: "
                "The server could not verify that you are authorized to "
                "access the URL requested. You either supplied the wrong "
                "credentials (e.g. a bad password), or your browser doesn't "
                "understand how to supply the credentials required.",
            )

    def test_invalid_validation_chain(self):
        validator1 = self._create_validator("validator")
        validator2 = self._create_validator("validator2")
        validator3 = self._create_validator("validator3")

        validator1.next_validator_id = validator2
        validator2.next_validator_id = validator3
        with self.assertRaises(ValidationError) as error:
            validator3.next_validator_id = validator1
        self.assertEqual(
            str(error.exception),
            "Validators mustn't make a closed chain: "
            "validator3 -> validator -> validator2 -> validator3.",
        )

    def test_invalid_validation_auto_chain(self):
        validator = self._create_validator("validator")
        with self.assertRaises(ValidationError) as error:
            validator.next_validator_id = validator
        self.assertEqual(
            str(error.exception),
            "Validators mustn't make a closed chain: " "validator -> validator.",
        )

    def test_partner_id_strategy_email_found(self):
        partner = self.env["res.partner"].search([("email", "!=", False)])[0]
        self._create_validator("validator6")
        authorization = "Bearer " + self._create_token(email=partner.email)
        with self._mock_request(authorization=authorization) as request:
            self.env["ir.http"]._auth_method_jwt_validator6()
            self.assertEqual(request.jwt_partner_id, partner.id)

    def test_partner_id_strategy_email_not_found(self):
        self._create_validator("validator6")
        authorization = "Bearer " + self._create_token(email="notanemail@example.com")
        with self._mock_request(authorization=authorization) as request:
            self.env["ir.http"]._auth_method_jwt_validator6()
            self.assertFalse(request.jwt_partner_id)

    def test_partner_id_strategy_email_not_found_partner_required(self):
        self._create_validator("validator6", partner_id_required=True)
        authorization = "Bearer " + self._create_token(email="notanemail@example.com")
        with self._mock_request(authorization=authorization):
            with self.assertRaises(UnauthorizedPartnerNotFound):
                self.env["ir.http"]._auth_method_jwt_validator6()

    def test_get_validator(self):
        AuthJwtValidator = self.env["auth.jwt.validator"]
        AuthJwtValidator.search([]).unlink()
        with (
            self.assertRaises(JwtValidatorNotFound),
            mute_logger("odoo.addons.auth_jwt.models.auth_jwt_validator"),
        ):
            AuthJwtValidator._get_validator_by_name(None)
        with (
            self.assertRaises(JwtValidatorNotFound),
            mute_logger("odoo.addons.auth_jwt.models.auth_jwt_validator"),
        ):
            AuthJwtValidator._get_validator_by_name("notavalidator")
        validator1 = self._create_validator(name="validator1")
        with (
            self.assertRaises(JwtValidatorNotFound),
            mute_logger("odoo.addons.auth_jwt.models.auth_jwt_validator"),
        ):
            AuthJwtValidator._get_validator_by_name("notavalidator")
        self.assertEqual(AuthJwtValidator._get_validator_by_name(None), validator1)
        self.assertEqual(
            AuthJwtValidator._get_validator_by_name("validator1"), validator1
        )
        # create a second validator
        validator2 = self._create_validator(name="validator2")
        with (
            self.assertRaises(AmbiguousJwtValidator),
            mute_logger("odoo.addons.auth_jwt.models.auth_jwt_validator"),
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
        self.assertFalse(
            hasattr(IrHttp.__class__, "_auth_method_public_or_jwt_validator1")
        )
        self._create_validator("validator1")
        self.assertTrue(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))
        self.assertTrue(
            hasattr(IrHttp.__class__, "_auth_method_public_or_jwt_validator1")
        )

    def test_auth_method_unregistration_on_unlink(self):
        IrHttp = self.env["ir.http"]
        validator = self._create_validator("validator1")
        self.assertTrue(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))
        self.assertTrue(
            hasattr(IrHttp.__class__, "_auth_method_public_or_jwt_validator1")
        )
        validator.unlink()
        self.assertFalse(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))
        self.assertFalse(
            hasattr(IrHttp.__class__, "_auth_method_public_or_jwt_validator1")
        )

    def test_auth_method_registration_on_rename(self):
        IrHttp = self.env["ir.http"]
        validator = self._create_validator("validator1")
        self.assertTrue(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))
        self.assertTrue(
            hasattr(IrHttp.__class__, "_auth_method_public_or_jwt_validator1")
        )
        validator.name = "validator2"
        self.assertFalse(hasattr(IrHttp.__class__, "_auth_method_jwt_validator1"))
        self.assertFalse(
            hasattr(IrHttp.__class__, "_auth_method_public_or_jwt_validator1")
        )
        self.assertTrue(hasattr(IrHttp.__class__, "_auth_method_jwt_validator2"))
        self.assertTrue(
            hasattr(IrHttp.__class__, "_auth_method_public_or_jwt_validator2")
        )

    def test_name_check(self):
        with self.assertRaises(ValidationError):
            self._create_validator(name="not an identifier")

    def test_public_or_jwt_valid_token(self):
        self._create_validator("validator")
        authorization = "Bearer " + self._create_token()
        with self._mock_request(authorization=authorization) as request:
            self.env["ir.http"]._auth_method_public_or_jwt_validator()
            assert request.jwt_payload["aud"] == "me"
