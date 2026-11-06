# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
        # since 20.0 the website model is declared in base, so its presence in
        # the registry no longer tells whether the website module is installed
        if "auth_signup_uninvited" in self.env["website"]._fields:
            # Enable public signup in website if it is installed; otherwise
            # tests here would fail
            current_website = self.env.website or self.env.ref("base.default_website")
            current_website.auth_signup_uninvited = "b2c"
        self.env["ir.config_parameter"].set_str("auth_signup.invitation_scope", "b2c")
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
