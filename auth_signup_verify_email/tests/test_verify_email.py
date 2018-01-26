# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml.html import document_fromstring
from odoo import _
from odoo.tests.common import HttpCase
from odoo.tools.misc import mute_logger


class UICase(HttpCase):
    def setUp(self):
        super(UICase, self).setUp()
        with self.cursor() as cr:
            env = self.env(cr)
            icp = env["ir.config_parameter"]
            icp.set_param("auth_signup.allow_uninvited", "True")

        self.data = {
            "csrf_token": self.csrf_token(),
            "name": "Somebody",
        }
        self.msg = {
            "badmail": _("That does not seem to be an email address."),
            "failure": _(
                "Something went wrong, please try again later or contact us."),
            "success": _("Check your email to activate your account!"),
        }

    def html_doc(self, url="/web/signup", data=None, timeout=30):
        """Get an HTML LXML document."""
        resp = self.url_open(url, data=data, timeout=timeout)
        return document_fromstring(resp.content)

    def csrf_token(self):
        """Get a valid CSRF token."""
        doc = self.html_doc()
        return doc.xpath("//input[@name='csrf_token']")[0].get("value")

    def search_text(self, doc, text):
        """Search for any element containing the text."""
        return doc.xpath("//*[contains(text(), '%s')]" % text)

    def test_bad_email(self):
        """Test rejection of bad emails."""
        self.data["login"] = "bad email"
        doc = self.html_doc(data=self.data)
        self.assertTrue(self.search_text(doc, self.msg["badmail"]))

    @mute_logger('odoo.addons.auth_signup_verify_email.controllers.main')
    def test_good_email(self):
        """Test acceptance of good emails.

        This test could lead to success if your SMTP settings are correct, or
        to failure otherwise. Any case is expected, since tests usually run
        under unconfigured demo instances.
        """
        self.data["login"] = "good@example.com"
        doc = self.html_doc(data=self.data)
        self.assertTrue(
            self.search_text(doc, self.msg["failure"]) or
            self.search_text(doc, self.msg["success"]))
