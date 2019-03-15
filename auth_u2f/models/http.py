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

import werkzeug.urls
import werkzeug.utils

from odoo import api, models
from odoo.http import HttpRequest, request


class U2FAuthenticationError(Exception):
    pass


_handle_exception_super = HttpRequest._handle_exception


# this is triggered when visiting non-public routes
def __handle_exception(self, exception):
    try:
        return _handle_exception_super(self, exception)
    except U2FAuthenticationError:
        redirect = None
        req = request.httprequest
        if req.method == 'POST':
            request.session.save_request_data()
            redirect = '/web/proxy/post{r.full_path}'.format(r=req)
        elif not request.params.get('noredirect'):
            redirect = req.url
        if redirect:
            query = werkzeug.urls.url_encode({
                'redirect': redirect,
            })
        return werkzeug.utils.redirect('/web/u2f/login?%s' % query)


HttpRequest._handle_exception = __handle_exception


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, auth_method='user'):
        # super should raise if 1st factor fails
        res = super(IrHttp, cls)._authenticate(auth_method=auth_method)

        if auth_method == 'user':
            cr = cls.pool.cursor()
            try:
                env = api.Environment(cr, request.session.uid, {})
                user = env['res.users'].browse(request.session.uid)
                if user._u2f_get_device():
                    user.u2f_check_credentials(
                        request.session.u2f_last_challenge,
                        request.session.u2f_token_response)
            finally:
                cr.close()

        return res
