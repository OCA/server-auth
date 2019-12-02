# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class AuthSmsAuthSignup(AuthSignupHome):
    @http.route()
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get('token') or qcontext.get('error'):
            return super(AuthSmsAuthSignup, self).web_auth_reset_password(
                *args, **kw
            )
        partner = request.env['res.partner'].sudo()._signup_retrieve_partner(
            qcontext['token'],
        )
        user = partner.user_ids[:1]
        if request.httprequest.method == 'POST' and kw.get(
                'auth_sms_request_code'
        ):
            try:
                request.env['res.users'].sudo()._auth_sms_send(user.id)
                qcontext['auth_sms_code_requested'] = True
            except Exception as e:
                qcontext['error'] = e.message or e
        elif request.httprequest.method == 'POST' and kw.get('auth_sms_code'):
            request.session['auth_sms.code'] = kw['auth_sms_code']
            try:
                user.sudo(user)._auth_sms_check_credentials()
            except Exception as e:
                del request.session['auth_sms.code']
                qcontext['error'] = e.message or e
            if request.session.get('auth_sms.code'):
                return super(AuthSmsAuthSignup, self).web_auth_reset_password(
                    *args, **kw
                )
        return request.render('auth_signup.reset_password', qcontext)
