# © initOS GmbH 2019
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, http, _
from odoo.http import request

from odoo.addons.web.controllers.main import Home
from ..exceptions import OTPLoginNeeded


class AuthAdminPasskey(Home):
    @http.route()
    def web_login(self, *args, **kwargs):
        try:
            response = super(AuthAdminPasskey, self).web_login(*args, **kwargs)
        except OTPLoginNeeded:
            request.session.update({
                'otp_login_needed': False,
                'login': kwargs.get('login', None),
                'password': kwargs.get('password', None),
            })
            return http.local_redirect(
                '/auth_admin_passkey/login',
                query={'redirect': request.params.get('redirect')},
                keep_hash=True,
            )

        return response

    @http.route(
        '/auth_admin_passkey/login', type='http', auth='public',
        methods=['GET'], website=True)
    def passkey_login_get(self, *args, **kwargs):
        return request.render(
            'auth_admin_passkey.otp_login', qcontext=request.params)

    @http.route(
        '/auth_admin_passkey/login', type='http', auth='none',
        methods=['POST'])
    def passkey_login_post(self, *args, **kwargs):
        user_model_sudo = request.env['res.users'].sudo()

        user_login = request.session.get('login')
        password = request.session.get('password')
        user = user_model_sudo.search([('login', '=', user_login)])
        now = fields.Datetime.now()
        if user.passkey_otp_expire and now < user.passkey_otp_expire:
            otp_code = request.params.get('confirmation_code')
            if user.passkey_otp and otp_code == user.passkey_otp:
                request.session['admin_passkey_with_otp'] = user.id
                request.session.authenticate(request.db, user.login, password)
                return http.redirect_with_hash('/web')

        return http.local_redirect(
            '/web/login',
            query={
                'redirect': request.params.get('redirect'),
                'error': _('The confirmation code is wrong.'),
            },
            keep_hash=True,
        )
