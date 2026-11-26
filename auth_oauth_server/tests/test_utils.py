# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from unittest import mock

from odoo.tests.common import TransactionCase

from .. import utils


class FakeResponse:
    def __init__(self, status=200, content_type="application/json", body=b"{}"):
        self.status_code = status
        self.headers = {"Content-Type": content_type, "Cache-Control": "max-age=60"}
        self.body = body
        self.closed = False

    def iter_content(self, chunk_size=1):
        for start in range(0, len(self.body), chunk_size):
            yield self.body[start : start + chunk_size]

    def close(self):
        self.closed = True


class TestUtils(TransactionCase):
    def test_redirect_uri_validity(self):
        valid = [
            "https://app.example.com/callback",
            "https://app.example.com/callback?tenant=1",
            "http://localhost:3000/callback",
            "http://127.0.0.1/callback",
            "http://[::1]:8080/callback",
        ]
        invalid = [
            "http://app.example.com/callback",
            "https://app.example.com/callback#fragment",
            "https://user:pass@app.example.com/callback",
            "https://app.example.com/call back",
            "https://app.example.com:99999/callback",
            "myapp://callback",
            "",
            None,
            "https://" + "a" * 3000,
        ]
        for uri in valid:
            self.assertTrue(utils.is_valid_redirect_uri(uri), uri)
        for uri in invalid:
            self.assertFalse(utils.is_valid_redirect_uri(uri), uri)

    def test_redirect_uri_matching(self):
        match = utils.redirect_uri_matches
        self.assertTrue(match("https://a.example.com/cb", "https://a.example.com/cb"))
        self.assertFalse(match("https://a.example.com/cb", "https://a.example.com/cb/"))
        self.assertFalse(
            match("https://a.example.com/cb", "https://a.example.com:444/cb")
        )
        # the port of loopback redirect URIs may vary (RFC 8252)
        self.assertTrue(match("http://127.0.0.1/cb", "http://127.0.0.1:51234/cb"))
        self.assertTrue(match("http://localhost:1/cb", "http://localhost:2/cb"))
        self.assertFalse(match("http://127.0.0.1/cb", "http://localhost:51234/cb"))
        self.assertFalse(match("http://127.0.0.1/cb", "http://127.0.0.1:5/other"))

    def test_add_query_keeps_existing_query(self):
        uri = utils.add_query(
            "https://a.example.com/cb?tenant=1", {"code": "x y", "state": None}
        )
        self.assertEqual(uri, "https://a.example.com/cb?tenant=1&code=x+y")

    def test_normalize_uri(self):
        self.assertEqual(
            utils.normalize_uri("HTTPS://ERP.Example.com/mcp/"),
            "https://erp.example.com/mcp",
        )
        self.assertEqual(utils.normalize_uri("erp.example.com"), "")
        self.assertEqual(utils.normalize_uri(None), "")

    def test_pkce(self):
        verifier = "a" * 43
        challenge = utils.pkce_s256(verifier)
        self.assertTrue(utils.check_pkce(verifier, challenge))
        self.assertFalse(utils.check_pkce("b" * 43, challenge))
        self.assertFalse(utils.check_pkce("short", utils.pkce_s256("short")))
        self.assertFalse(utils.check_pkce(None, challenge))

    def test_sign_verify(self):
        signed = utils.sign("secret", "scope", {"uid": 2}, 60)
        self.assertEqual(utils.verify("secret", "scope", signed)["uid"], 2)
        self.assertIsNone(utils.verify("other", "scope", signed))
        self.assertIsNone(utils.verify("secret", "other", signed))
        body, signature = signed.split(".")
        self.assertIsNone(utils.verify("secret", "scope", body + "x." + signature))
        self.assertIsNone(utils.verify("secret", "scope", "garbage"))
        expired = utils.sign("secret", "scope", {"uid": 2}, -1)
        self.assertIsNone(utils.verify("secret", "scope", expired))

    def test_metadata_document_url(self):
        check = utils.check_metadata_document_url
        self.assertTrue(check("https://app.example.com/oauth/client.json"))
        self.assertTrue(check("https://app.example.com/client?v=1"))
        for url in (
            "http://app.example.com/client.json",
            "https://app.example.com",
            "https://app.example.com/",
            "https://app.example.com:8443/client.json",
            "https://user@app.example.com/client.json",
            "https://app.example.com/client.json#x",
            "https://93.184.216.34/client.json",
            "https://[2001:db8::1]/client.json",
            "https://app.example.com/a/../client.json",
            "https://app.example.com/a/%2e%2e/client.json",
        ):
            self.assertFalse(check(url), url)

    def test_public_address(self):
        self.assertTrue(utils.is_public_address("93.184.216.34"))
        self.assertTrue(utils.is_public_address("2606:2800:220:1:248:1893:25c8:1946"))
        for address in (
            "127.0.0.1",
            "10.1.2.3",
            "192.168.1.1",
            "169.254.169.254",
            "::1",
            "fe80::1",
            "fe80::1%eth0",
            "::ffff:127.0.0.1",
            "64:ff9b::a01:203",
            "2002:a01:203::1",
            "not an address",
        ):
            self.assertFalse(utils.is_public_address(address), address)

    def test_max_age(self):
        self.assertEqual(utils.max_age_from_cache_control("max-age=600"), 600)
        self.assertEqual(utils.max_age_from_cache_control("max-age=5"), 300)
        self.assertEqual(utils.max_age_from_cache_control("max-age=999999"), 86400)
        self.assertEqual(utils.max_age_from_cache_control("no-store"), 300)
        self.assertEqual(utils.max_age_from_cache_control(""), 3600)

    def _fetch(self, response):
        with mock.patch.object(utils.requests, "get", return_value=response) as get:
            try:
                return utils.fetch_metadata_document("https://app.example.com/c.json")
            finally:
                self.assertTrue(response.closed)
                kwargs = get.call_args[1]
                self.assertFalse(kwargs["allow_redirects"])
                self.assertTrue(kwargs["timeout"])

    def test_fetch_metadata_document(self):
        document, cache_control = self._fetch(FakeResponse(body=b'{"a": 1}'))
        self.assertEqual(document, {"a": 1})
        self.assertEqual(cache_control, "max-age=60")
        for response in (
            FakeResponse(status=302),
            FakeResponse(content_type="text/html"),
            FakeResponse(body=b"{" + b" " * 6000 + b"}"),
            FakeResponse(body=b"not json"),
        ):
            with self.assertRaises(ValueError):
                self._fetch(response)
