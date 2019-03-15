# Copyright (C) 2017 Joren Van Onder
# Copyright (C) 2019 initOS GmbH

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

import json
import werkzeug.utils

from odoo import http
from odoo.addons.web.controllers.main import Home
from odoo.http import request
from odoo.exceptions import AccessDenied
from ..models.http import U2FAuthenticationError


class AuthU2FController(Home):
    @http.route('/web/u2f/login', type='http', auth='none', sitemap=False)
    def u2f_login(self, u2f_token_response=None, redirect=None, **kw):
        user = request.env['res.users'].browse(request.session.uid)
        user = user.sudo(request.session.uid)

        if not user or not user._u2f_get_device():
            raise AccessDenied()

        if request.httprequest.method == 'POST':
            request.session.u2f_token_response = u2f_token_response
            return http.redirect_with_hash(self._login_redirect(
                user.id, redirect=redirect))
        else:
            login_challenge = user._u2f_get_login_challenge()
            if not login_challenge:
                raise AccessDenied()

            request.session.u2f_last_challenge = login_challenge.json
            return request.render('auth_u2f.login', {
                'login_data': json.dumps(login_challenge.data_for_client),
                'redirect': redirect,
            })


class U2FLogin(Home):
    # necessary because '/web' route has auth="none"
    @http.route()
    def web_client(self, s_action=None, **kw):
        response = super(U2FLogin, self).web_client(s_action=s_action, **kw)

        try:
            request.env['ir.http']._authenticate()
        except U2FAuthenticationError:
            return werkzeug.utils.redirect('/web/u2f/login', 303)

        return response
