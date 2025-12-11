# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from lxml.html import document_fromstring

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
        self.assertTrue(
            doc.xpath('//p[@class="alert alert-danger"]'),
            msg="Expected an error for an invalid email.",
        )

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_good_email(self):
        """Test acceptance of good emails."""
        self.data["login"] = "contributors@odoo-community.org"
        doc = self.html_doc(data=self.data)
        self.assertTrue(
            doc.xpath('//p[@class="alert alert-success"]'),
            msg="Expected a success message for a valid email.",
        )

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_email_undeliverable(self):
        """Test rejection of undeliverable emails."""
        self.data["login"] = "test@yyyy.invalid"
        doc = self.html_doc(data=self.data)
        self.assertGreater(
            len(doc.xpath('//p[@class="alert alert-danger"]')),
            0,
            msg="Expected an error for an undeliverable email.",
        )

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_duplicate_user_registration(self):
        """Test rejection of duplicate email registration."""
        test_email = "existing@odoo-community.org"
        self.env["res.users"].create({"name": "Test User", "login": test_email})
        # Mock signup to raise an exception (simulating duplicate key error)
        with patch(
            "odoo.addons.auth_signup.models.res_users.ResUsers.signup",
            side_effect=Exception("Duplicate key error"),
        ):
            self.data["login"] = test_email
            doc = self.html_doc(data=self.data)
            error_messages = doc.xpath('//p[@class="alert alert-danger"]/text()')
            self.assertGreater(
                len(error_messages),
                0,
                msg="Expected an error for a duplicate email.",
            )
            self.assertIn(
                "already registered",
                str(error_messages[0]).lower(),
                msg="Expected the duplicate email message to "
                "say the email is already registered.",
            )

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_signup_with_existing_email_field(self):
        """Test signup when email field is already provided."""
        self.data["login"] = "newuser@odoo-community.org"
        self.data["email"] = "newuser@odoo-community.org"
        doc = self.html_doc(data=self.data)
        self.assertFalse(
            doc.xpath('//p[@class="alert alert-danger"]'),
            msg="Should not show an error when login and email are valid.",
        )

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_signup_without_email_field(self):
        """Test signup when email field is not provided (uses login as email)."""
        self.data["login"] = "newuser2@odoo-community.org"
        if "email" in self.data:
            del self.data["email"]
        doc = self.html_doc(data=self.data)
        self.assertFalse(
            doc.xpath('//p[@class="alert alert-danger"]'),
            msg="Should not show an error when email is "
            "missing but login is a valid email.",
        )

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_generic_exception(self):
        """Test generic exception branch."""
        with patch(
            "odoo.addons.auth_signup_verify_email.controllers.main.validate_email",
            side_effect=Exception("Generic error"),
        ):
            self.data["login"] = "error@odoo-community.org"
            doc = self.html_doc(data=self.data)
            self.assertTrue(
                doc.xpath('//p[@class="alert alert-danger"]'),
                msg="Expected a generic error alert when "
                "validate_email raises an exception.",
            )
