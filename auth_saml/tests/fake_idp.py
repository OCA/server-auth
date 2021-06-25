import os
from urllib.parse import parse_qs, urlparse

from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT, pack
from saml2.authn_context import INTERNETPROTOCOLPASSWORD
from saml2.config import Config as Saml2Config
from saml2.metadata import create_metadata_string
from saml2.saml import NAME_FORMAT_URI, NAMEID_FORMAT_PERSISTENT
from saml2.server import Server

TYP = {"GET": [BINDING_HTTP_REDIRECT], "POST": [BINDING_HTTP_POST]}


AUTHN = {
    "class_ref": INTERNETPROTOCOLPASSWORD,
    "authn_auth": "http://www.example.com/login",
}


BASE = "http://localhost:8000"
CONFIG = {
    "entityid": "urn:mace:example.com:saml:example:idp",
    "name": "Rolands IdP",
    "service": {
        "aa": {
            "endpoints": {
                "attribute_service": [
                    ("%s/aap" % BASE, BINDING_HTTP_POST),
                ]
            },
        },
        "aq": {
            "endpoints": {
                "authn_query_service": [("%s/aqs" % BASE, BINDING_HTTP_POST)]
            },
        },
        "idp": {
            "endpoints": {
                "single_sign_on_service": [
                    ("%s/sso/redirect" % BASE, BINDING_HTTP_REDIRECT),
                    ("%s/sso/post" % BASE, BINDING_HTTP_POST),
                ],
            },
            "policy": {
                "default": {
                    "lifetime": {"minutes": 15},
                    "attribute_restrictions": None,
                    "name_form": NAME_FORMAT_URI,
                },
                "urn:mace:example.com:saml:example:sp": {
                    "lifetime": {"minutes": 5},
                    "nameid_format": NAMEID_FORMAT_PERSISTENT,
                },
            },
        },
    },
    "debug": 1,
    "key_file": os.path.join(os.path.dirname(__file__), "data", "idp.pem"),
    "cert_file": os.path.join(os.path.dirname(__file__), "data", "idp.pem"),
    "organization": {
        "name": "Example",
        "display_name": [("Example", "uk")],
        "url": "http://www.example.com/",
    },
    "contact_person": [
        {
            "given_name": "Admin",
            "sur_name": "Admin",
            "email_address": ["admin@example.com"],
            "contact_type": "technical",
        },
    ],
}


class DummyResponse(object):
    def __init__(self, status, data, headers=None):
        self.status_code = status
        self.text = data
        self.headers = headers or []
        self.content = data

    def _unpack(self, ver="SAMLResponse"):
        """
        Unpack the response form
        """
        _str = self.text

        SR_STR = 'name="%s" value="' % ver
        RS_STR = 'name="RelayState" value="'

        i = _str.find(SR_STR)
        i += len(SR_STR)
        j = _str.find('"', i)

        sr = _str[i:j]

        start = _str.find(RS_STR, j)
        start += len(RS_STR)
        end = _str.find('"', start)

        rs = _str[start:end]

        return {ver: sr, "RelayState": rs}


class FakeIDP(Server):
    def __init__(self, metadatas=None):
        settings = CONFIG
        if metadatas:
            settings.update({"metadata": {"inline": metadatas}})

        config = Saml2Config()
        config.load(settings)
        config.allow_unknown_attributes = True
        Server.__init__(self, config=config)

    def get_metadata(self):
        return create_metadata_string(
            None,
            config=self.config,
            sign=True,
            valid=True,
            cert=CONFIG.get("cert_file"),
            keyfile=CONFIG.get("key_file"),
        )

    def fake_login(self, url):
        # Assumes GET query and HTTP_REDIRECT only.
        # This is all that auth_pysaml currently supports.
        parsed_url = urlparse(url)
        qs_dict = parse_qs(parsed_url.query)

        samlreq = qs_dict["SAMLRequest"][0]
        rstate = qs_dict["RelayState"][0]

        # process the logon request, and automatically "login"
        return self.authn_request_endpoint(samlreq, BINDING_HTTP_REDIRECT, rstate)

    def authn_request_endpoint(self, req, binding, relay_state):
        req = self.parse_authn_request(req, binding)
        if req.message.protocol_binding == BINDING_HTTP_REDIRECT:
            _binding = BINDING_HTTP_POST
        else:
            _binding = req.message.protocol_binding

        try:
            resp_args = self.response_args(req.message, [_binding])
        except Exception:
            raise

        identity = {
            "surName": "Example",
            "givenName": "Test",
            "title": "Ind",
            "mail": "test@example.com",
        }

        resp_args.update({"sign_assertion": True, "sign_response": True})

        authn_resp = self.create_authn_response(
            identity, userid=identity.get("mail"), authn=AUTHN, **resp_args
        )

        _dict = pack.factory(
            _binding, authn_resp, resp_args["destination"], relay_state, "SAMLResponse"
        )

        return DummyResponse(**_dict)
