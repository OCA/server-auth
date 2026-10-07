# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import timedelta
from unittest import mock

import requests

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

from .. import utils
from ..exceptions import OAuthError
from . import common

DOCUMENT_URL = "https://app.example.com/oauth/client.json"
PUBLIC_ADDRESS = "93.184.216.34"


def metadata_document(**values):
    return dict(
        {
            "client_id": DOCUMENT_URL,
            "client_name": "Example Client",
            "client_uri": "https://app.example.com",
            "redirect_uris": ["http://127.0.0.1/callback"],
            "token_endpoint_auth_method": "none",
        },
        **values
    )


@tagged("post_install", "-at_install")
class TestRegistration(common.OAuthServerMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setup_oauth_server()
        cls.clients = cls.env["oauth.server.client"]

    def assertOAuthError(self, error, function, *args, **kwargs):
        with self.assertRaises(OAuthError) as raised:
            function(*args, **kwargs)
        self.assertEqual(raised.exception.error, error, raised.exception.description)

    # ------------------------------------------------------------------
    # Dynamic client registration
    # ------------------------------------------------------------------

    def test_register_public_client(self):
        response = self.clients._register_dynamic(
            {
                "client_name": "Desktop App",
                "redirect_uris": ["http://localhost:3000/callback"],
                "token_endpoint_auth_method": "none",
                "grant_types": ["authorization_code", "refresh_token"],
                "software_id": "ignored",
            }
        )
        client = self.clients.search([("identifier", "=", response["client_id"])])
        self.assertEqual(client.registration_type, "dynamic")
        self.assertEqual(client.client_type, "public")
        self.assertEqual(client.name, "Desktop App")
        self.assertNotIn("client_secret", response)
        self.assertEqual(response["token_endpoint_auth_method"], "none")
        self.assertEqual(response["response_types"], ["code"])

    def test_register_confidential_client(self):
        response = self.clients._register_dynamic(
            {
                "redirect_uris": ["https://web.example.com/callback"],
                "token_endpoint_auth_method": "client_secret_post",
                "client_uri": "http://not-https.example.com",
            }
        )
        client = self.clients.search([("identifier", "=", response["client_id"])])
        self.assertEqual(client.client_type, "confidential")
        # no client_name: the redirect host stands in for it
        self.assertEqual(client.name, "web.example.com")
        self.assertFalse(client.client_uri)
        self.assertEqual(response["client_secret_expires_at"], 0)
        self.assertEqual(
            self.env["oauth.server"]._authenticate_client(
                response["client_id"], response["client_secret"]
            ),
            client,
        )

    def test_register_errors(self):
        uris = ["https://web.example.com/callback"]
        cases = [
            ("invalid_client_metadata", ["not", "an", "object"]),
            ("invalid_redirect_uri", {}),
            ("invalid_redirect_uri", {"redirect_uris": []}),
            ("invalid_redirect_uri", {"redirect_uris": "https://a.example.com/cb"}),
            ("invalid_redirect_uri", {"redirect_uris": ["http://web.example.com/cb"]}),
            ("invalid_redirect_uri", {"redirect_uris": uris * 11}),
            (
                "invalid_client_metadata",
                {
                    "redirect_uris": uris,
                    "token_endpoint_auth_method": "private_key_jwt",
                },
            ),
            (
                "invalid_client_metadata",
                {"redirect_uris": uris, "grant_types": ["client_credentials"]},
            ),
            (
                "invalid_client_metadata",
                {"redirect_uris": uris, "response_types": ["token"]},
            ),
            (
                "invalid_client_metadata",
                {"redirect_uris": uris, "client_name": "x" * 201},
            ),
        ]
        for error, metadata in cases:
            with self.subTest(metadata=metadata):
                self.assertOAuthError(error, self.clients._register_dynamic, metadata)

    # ------------------------------------------------------------------
    # Client ID Metadata Documents
    # ------------------------------------------------------------------

    def patch_network(self, document=None, addresses=None, error=None):
        fetch = mock.patch.object(
            utils,
            "fetch_metadata_document",
            side_effect=error,
            return_value=(document or metadata_document(), "max-age=600"),
        )
        resolve = mock.patch.object(
            utils, "resolve_host", return_value=addresses or {PUBLIC_ADDRESS}
        )
        return fetch, resolve

    def get_client(self, url=DOCUMENT_URL, **kwargs):
        fetch, resolve = self.patch_network(**kwargs)
        with fetch as fetched, resolve:
            client = self.clients._get_for_authorization(url)
        return client, fetched

    def test_metadata_document(self):
        client, fetched = self.get_client()
        fetched.assert_called_once_with(DOCUMENT_URL)
        self.assertEqual(client.identifier, DOCUMENT_URL)
        self.assertEqual(client.registration_type, "metadata_document")
        self.assertEqual(client.client_type, "public")
        self.assertEqual(client.name, "Example Client")
        self.assertEqual(client._get_redirect_uris(), ["http://127.0.0.1/callback"])
        self.assertGreater(client.metadata_expires_at, fields.Datetime.now())
        # cached while fresh
        same, fetched = self.get_client()
        self.assertEqual(same, client)
        fetched.assert_not_called()
        # fetched again once expired
        client.metadata_expires_at = fields.Datetime.now() - timedelta(seconds=1)
        same, fetched = self.get_client(
            document=metadata_document(client_name="Renamed")
        )
        fetched.assert_called_once_with(DOCUMENT_URL)
        self.assertEqual(same, client)
        self.assertEqual(client.name, "Renamed")

    def test_metadata_document_errors(self):
        cases = [
            {"document": metadata_document(client_id="https://other.example.com/c")},
            {"document": metadata_document(client_name="")},
            {"document": metadata_document(redirect_uris=["http://evil.com/cb"])},
            {
                "document": metadata_document(
                    token_endpoint_auth_method="client_secret_basic"
                )
            },
            {"document": ["not", "a", "dict"]},
            {"addresses": {"10.0.0.5"}},
            {"addresses": {PUBLIC_ADDRESS, "127.0.0.1"}},
            {"error": requests.ConnectionError("down")},
            {"error": ValueError("too large")},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                fetch, resolve = self.patch_network(**kwargs)
                with fetch, resolve:
                    self.assertOAuthError(
                        "invalid_client",
                        self.clients._get_for_authorization,
                        DOCUMENT_URL,
                    )
        self.assertFalse(self.clients.search([("identifier", "=", DOCUMENT_URL)]))

    def test_metadata_document_not_a_url(self):
        fetch, resolve = self.patch_network()
        with fetch as fetched, resolve:
            for identifier in ("http://app.example.com/c.json", "unknown-client"):
                self.assertOAuthError(
                    "invalid_client", self.clients._get_for_authorization, identifier
                )
        fetched.assert_not_called()

    def test_metadata_document_disabled(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("auth_oauth_server.cimd_enabled", False)
        fetch, resolve = self.patch_network()
        with fetch as fetched, resolve:
            self.assertOAuthError(
                "invalid_client", self.clients._get_for_authorization, DOCUMENT_URL
            )
        fetched.assert_not_called()
        self.assertFalse(
            self.env["oauth.server"]._metadata()[
                "client_id_metadata_document_supported"
            ]
        )

    def test_metadata_document_trusted_domains(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param(
            "auth_oauth_server.cimd_trusted_domains", "other.com, .example.com"
        )
        client, _fetched = self.get_client()
        self.assertTrue(client)
        params.set_param("auth_oauth_server.cimd_trusted_domains", "other.com")
        fetch, resolve = self.patch_network()
        with fetch, resolve:
            self.assertOAuthError(
                "invalid_client",
                self.clients._get_for_authorization,
                "https://evil.example.org/client.json",
            )

    def test_disabled_metadata_document_client(self):
        client, _fetched = self.get_client()
        client.active = False
        fetch, resolve = self.patch_network()
        with fetch, resolve:
            self.assertOAuthError(
                "unauthorized_client", self.clients._get_for_authorization, DOCUMENT_URL
            )

    # ------------------------------------------------------------------
    # Garbage collection
    # ------------------------------------------------------------------

    def test_unused_clients_are_forgotten(self):
        response = self.clients._register_dynamic(
            {"redirect_uris": ["https://web.example.com/callback"]}
        )
        unused = self.clients.search([("identifier", "=", response["client_id"])])
        response = self.clients._register_dynamic(
            {"redirect_uris": ["https://web.example.com/callback"]}
        )
        used = self.clients.search([("identifier", "=", response["client_id"])])
        self.approve(client=used)
        clients = unused | used | self.client
        clients.flush_recordset()
        self.env.cr.execute(
            "UPDATE oauth_server_client SET create_date = %s WHERE id IN %s",
            (fields.Datetime.now() - timedelta(days=2), tuple(clients.ids)),
        )
        self.clients._gc_unused_clients()
        self.assertFalse(unused.exists())
        self.assertTrue(used.exists())
        # clients created by an administrator are kept
        self.assertTrue(self.client.exists())
