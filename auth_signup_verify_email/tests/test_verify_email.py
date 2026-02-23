# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml.html import document_fromstring

try:
    from unittest.mock import patch
except ImportError:
    from unittest.mock import patch

from odoo.exceptions import UserError
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

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_good_email_with_captcha_fields(self):
        """Test acceptance when captcha fields are present in POST data."""
        self.data["login"] = "contributors@odoo-community.org"
        self.data["turnstile_captcha"] = "dummy-turnstile-token"
        self.data["recaptcha_token_response"] = "dummy-recaptcha-token"
        doc = self.html_doc(data=self.data)
        self.assertTrue(doc.xpath('//p[@class="alert alert-success"]'))

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_captcha_verification_error(self):
        """Test rejection when captcha verification raises an error."""
        self.data["login"] = "contributors@odoo-community.org"
        with patch.object(
            type(self.env["ir.http"]),
            "_verify_request_recaptcha_token",
            side_effect=UserError("Captcha failed"),
            create=True,
        ):
            doc = self.html_doc(data=self.data)
        self.assertTrue(doc.xpath('//p[@class="alert alert-danger"]'))

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_captcha_verification_false(self):
        """Test rejection when captcha verification returns False."""
        self.data["login"] = "contributors@odoo-community.org"
        with patch.object(
            type(self.env["ir.http"]),
            "_verify_request_recaptcha_token",
            return_value=False,
            create=True,
        ):
            doc = self.html_doc(data=self.data)
        self.assertTrue(doc.xpath('//p[@class="alert alert-danger"]'))
