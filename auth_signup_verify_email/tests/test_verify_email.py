# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from mock import patch
from lxml.html import document_fromstring
from odoo.tests.common import at_install, post_install, HttpCase
from odoo.addons.mail.models import mail_template
from odoo.tools.misc import mute_logger


@at_install(False)
@post_install(True)
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

    @mute_logger('odoo.addons.auth_signup_verify_email.controllers.main')
    def test_good_email(self):
        """Test acceptance of good emails."""
        self.data["login"] = "good@example.com"
        doc = self.html_doc(data=self.data)
        self.assertTrue(doc.xpath('//p[@class="alert alert-success"]'))
