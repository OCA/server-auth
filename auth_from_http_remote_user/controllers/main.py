# Author: Laurent Mignon
# Copyright 2014-2018 'ACSONE SA/NV'
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging
import werkzeug

from odoo import http
from odoo import api
from odoo import SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers import main

from .. import utils

_logger = logging.getLogger(__name__)


class Home(main.Home):
    _REMOTE_USER_ATTRIBUTE = 'HTTP_REMOTE_USER'

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        main.ensure_db()
        try:
            self._bind_http_remote_user(http.request.session.db)
        except http.AuthenticationError:
            return werkzeug.exceptions.Unauthorized().get_response()
        return super().web_client(s_action, **kw)

    def search_user(self, users, login):
        """Search for an active user by login name"""
        user = users.sudo().search([
            ('login', '=', login),
            ('active', '=', True)],
            limit=1
        )
        if user:
            return user[0]
        return None

    def login_http_remote_user(self, env, user):
        """Specific login for HTTP user.

        Generate a key for authentication and update the user
        """
        key = utils.randomString(utils.KEY_LENGTH, '0123456789abcdef')
        user.with_env(env).sudo().write({'sso_key': key})
        return key

    def _bind_http_remote_user(self, db_name):
        headers = http.request.httprequest.headers.environ
        login = headers.get(self._REMOTE_USER_ATTRIBUTE, None)
        if not login:
            # No SSO user in header, continue usual behavior
            return
        request_login = request.session.login
        if request_login:
            if request_login == login:
                # Already authenticated
                return
            else:
                request.session.logout(keep_db=True)
        try:
            user = self.search_user(request.env['res.users'], login)
            if not user:
                # HTTP_REMOTE_USER login not found in database
                request.session.logout(keep_db=True)
                raise http.AuthenticationError()
            # Login SSO user using separate environment as the authentication
            # later on is done in a specific environment as well
            with api.Environment.manage():
                with request.env.registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    key = self.login_http_remote_user(env, user)
            request.session.authenticate(db_name, login=login,
                                         password=key, uid=user.id)
        except http.AuthenticationError as e:
            raise
        except Exception as e:
            _logger.error("Error binding HTTP remote user", exc_info=True)
            raise
