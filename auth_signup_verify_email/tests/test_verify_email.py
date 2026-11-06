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
        self.set_signup_scope("b2c")
        self.data = {
            "csrf_token": self.csrf_token(),
            "name": "Somebody",
        }

    def set_signup_scope(self, scope):
        # since 20.0 the website model is declared in base, so its presence in
        # the registry no longer tells whether the website module is installed
        if "auth_signup_uninvited" in self.env["website"]._fields:
            # Public signup is configured per website when it is installed
            current_website = self.env.website or self.env.ref("base.default_website")
            current_website.auth_signup_uninvited = scope
        self.env["ir.config_parameter"].set_str("auth_signup.invitation_scope", scope)

    def html_doc(self, url="/web/signup", data=None, timeout=30):
        """Get an HTML LXML document."""
        with patch(mail_template.__name__ + ".MailTemplate.send_mail"):
            resp = self.url_open(url, data=data, timeout=timeout)
        return document_fromstring(resp.content)

    def csrf_token(self):
        """Get a valid CSRF token."""
        doc = self.html_doc()
        return doc.xpath("//input[@name='csrf_token']")[0].get("value")

    def test_signup_page_hides_password(self):
        """Uninvited users sign up without choosing a password."""
        doc = self.html_doc()
        self.assertTrue(doc.xpath('//input[@name="login"]'))
        self.assertFalse(doc.xpath('//input[@name="password"]'))
        self.assertFalse(doc.xpath('//input[@name="confirm_password"]'))

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

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main", "odoo.sql_db")
    def test_duplicate_email(self):
        """Signing up twice with the same email is rejected."""
        self.data["login"] = "contributors@odoo-community.org"
        self.html_doc(data=self.data)
        doc = self.html_doc(data=self.data)
        error = doc.xpath('//p[@class="alert alert-danger"]')
        self.assertTrue(error)
        self.assertIn("Another user is already registered", error[0].text_content())
        users = self.env["res.users"].search([("login", "=", self.data["login"])])
        self.assertEqual(len(users), 1)

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_extra_params_ignored(self):
        """Only the signup form fields reach the new user."""
        self.data["login"] = "contributors@odoo-community.org"
        self.data["ref"] = "injected"
        self.html_doc(data=self.data)
        user = self.env["res.users"].search([("login", "=", self.data["login"])])
        self.assertTrue(user, "signup should have created the user")
        self.assertFalse(user.ref)

    def test_signup_disabled(self):
        """Passwordless signup follows core's 404 when signup is disabled."""
        self.set_signup_scope("b2b")
        self.data["login"] = "contributors@odoo-community.org"
        with patch(mail_template.__name__ + ".MailTemplate.send_mail"):
            resp = self.url_open("/web/signup", data=self.data, timeout=30)
        self.assertEqual(resp.status_code, 404)
        self.assertFalse(
            self.env["res.users"].search([("login", "=", self.data["login"])])
        )

    @mute_logger("odoo.addons.auth_signup_verify_email.controllers.main")
    def test_activation_page_asks_for_password(self):
        """The page linked in the activation email must let you set a password.

        This module hides the password fields on the public signup form, so the
        only place left to set one is the page the activation email points to.
        """
        self.data["login"] = "contributors@odoo-community.org"
        self.html_doc(data=self.data)
        user = self.env["res.users"].search([("login", "=", self.data["login"])])
        self.assertTrue(user, "signup should have created the user")
        user.partner_id.signup_prepare(signup_type="reset")
        url = user.partner_id.with_context(relative_url=True)._get_signup_url()
        doc = self.html_doc(url=url)
        self.assertTrue(doc.xpath('//input[@name="password"]'))
        self.assertTrue(doc.xpath('//input[@name="confirm_password"]'))
