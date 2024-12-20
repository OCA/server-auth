# Copyright (C) 2013-Today GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import hashlib
import logging
from datetime import datetime

from odoo import SUPERUSER_ID, _, api, exceptions, models
from odoo.http import request
from odoo.tools import config

logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _send_email_passkey(self, login_user):
        """Send a email to the system administrator and / or the user
        to inform passkey use."""
        MailMail = self.env["mail.mail"].with_user(SUPERUSER_ID)

        admin_user = self.with_user(SUPERUSER_ID).browse(SUPERUSER_ID)

        send_to_user = config.get("auth_admin_passkey_send_to_user", True)
        sysadmin_email = config.get("auth_admin_passkey_sysadmin_email", False)

        mails = []
        if sysadmin_email:
            lang = config.get("auth_admin_passkey_sysadmin_lang", admin_user.lang)
            mails.append({"email": sysadmin_email, "lang": lang})
        if send_to_user and login_user.email:
            mails.append({"email": login_user.email, "lang": login_user.lang})
        for mail in mails:
            subject, body_html = self._prepare_email_passkey(login_user)

            MailMail.create(
                {"email_to": mail["email"], "subject": subject, "body_html": body_html}
            )

    @api.model
    def _prepare_email_passkey(self, login_user):
        subject = _("Passkey used")
        body = _(
            "System Administrator user used his passkey to login"
            " with %(login)s."
            "\n\n\n\n"
            "Technicals informations belows : \n\n"
            "- Login date : %(login_date)s\n\n"
        ) % {
            "login": login_user.login,
            "login_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return subject, f"<pre>{body}</pre>"

    def _check_credentials(self, credential, env):
        try:
            return super()._check_credentials(credential, env)

        except exceptions.AccessDenied:
            # Just be sure that parent methods aren't wrong
            users = self.with_user(SUPERUSER_ID).search([("id", "=", self._uid)])
            if not users:
                raise

            file_password = config.get("auth_admin_passkey_password", False)

            password_encrypted = config.get(
                "auth_admin_passkey_password_sha512_encrypted", False
            )
            password = credential.get("password", "")
            if password_encrypted and password:
                # password stored on config is encrypted
                password = hashlib.sha512(password.encode()).hexdigest()

            if password and file_password == password:
                if request and hasattr(request, "session"):
                    ignore_totp = config.get("auth_admin_passkey_ignore_totp", False)
                    request.session["ignore_totp"] = ignore_totp
                self._send_email_passkey(users[0])
                return {
                    "uid": self.env.user.id,
                    "auth_method": "password",
                    "mfa": "default",
                }
            else:
                raise

    def _mfa_url(self):
        if request.session.get("ignore_totp"):
            return None
        return super()._mfa_url()
