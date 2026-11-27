# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from urllib.parse import urlencode

from lxml.html import document_fromstring

try:
    from unittest.mock import patch
except ImportError:
    from unittest.mock import patch

from odoo.tests.common import HttpCase
from odoo.tools.misc import mute_logger

from odoo.addons.mail.models import mail_template


class UICase(HttpCase):
    def setUp(self):
        super().setUp()
        if "website" in self.env:
            # Enable public signup in website if it is installed; otherwise
            # tests here would fail
            current_website = self.env["website"].get_current_website()
            current_website.auth_signup_uninvited = "b2c"
        self.env["ir.config_parameter"].set_param("auth_signup.invitation_scope", "b2c")
        self.data = {
            "csrf_token": self.csrf_token(),
            "name": "Somebody",
        }

    def html_doc(self, url="/web/signup", data=None, timeout=30):
        """Get an HTML LXML document."""
        with patch(mail_template.__name__ + ".MailTemplate.send_mail"):
            resp = self.url_open(url, data=data, timeout=timeout)
        return document_fromstring(resp.content)

    def csrf_token(self):
        """Get a valid CSRF token."""
        doc = self.html_doc()
        return doc.xpath("//input[@name='csrf_token']")[0].get("value")

    def test_bad_email(self):
        """Test rejection of bad emails."""
        self.data["login"] = "bad email"
        doc = self.html_doc(data=self.data)
        self.assertTrue(doc.xpath('//p[@class="alert alert-danger"]'))

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_good_email(self):
        """Test acceptance of good emails."""
        self.data["login"] = "contributors@odoo-community.org"
        doc = self.html_doc(data=self.data)
        self.assertTrue(doc.xpath('//p[@class="alert alert-success"]'))

    def assertPasswordFields(self, doc, present):
        for name in ("password", "confirm_password"):
            self.assertEqual(bool(doc.xpath(f"//input[@name='{name}']")), present)

    def test_password_fields_without_token(self):
        """Uninvited signup stays passwordless."""
        self.assertPasswordFields(self.html_doc(), False)
        doc = self.html_doc("/web/signup?" + urlencode({"token": "bad"}))
        self.assertPasswordFields(doc, False)

    def test_password_fields_with_token(self):
        """Token pages (activation, reset, invitation) show password fields."""
        partner = self.env["res.partner"].create(
            {"name": "Invited", "email": "invited@example.com"}
        )
        partner.signup_prepare()
        query = urlencode({"token": partner._generate_signup_token()})
        for url in ("/web/reset_password", "/web/signup"):
            with self.subTest(url=url):
                self.assertPasswordFields(self.html_doc(f"{url}?{query}"), True)
