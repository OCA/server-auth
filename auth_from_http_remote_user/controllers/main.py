# Author: Laurent Mignon
# Copyright 2014-2018 'ACSONE SA/NV'
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers import main
from odoo.addons.auth_from_http_remote_user.model import \
    AuthFromHttpRemoteUserInstalled
from .. import utils

import odoo
import random
import logging
import werkzeug

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
        return super(Home, self).web_client(s_action, **kw)

    def _search_user(self, res_users, login, cr):
        user_ids = request.env['res.users'].sudo().search([
            ('login', '=', login), ('active', '=', True)])
        assert len(user_ids) < 2
        if user_ids:
            return user_ids[0]
        return None

    def _bind_http_remote_user(self, db_name):
        try:
            registry = odoo.registry(db_name)
            with registry.cursor() as cr:
                if AuthFromHttpRemoteUserInstalled._name not in registry:
                    # module not installed in database, continue usual behavior
                    return

                headers = http.request.httprequest.headers.environ

                login = headers.get(self._REMOTE_USER_ATTRIBUTE, None)
                if not login:
                    # no HTTP_REMOTE_USER header, continue usual behavior
                    return

                request_login = request.session.login
                if request_login:
                    if request_login == login:
                        request.params['login_success'] = True
                        # already authenticated
                        return
                    else:
                        request.session.logout(keep_db=True)

                res_users = registry.get('res.users')
                user_id = self._search_user(res_users, login, cr)
                if not user_id:
                    # HTTP_REMOTE_USER login not found in database
                    request.session.logout(keep_db=True)
                    raise http.AuthenticationError()

                request.params['login_success'] = True
                # Generating a specific key for authentication
                # And updating the db directly as authentication is  done
                # in a separate  environment
                key = randomString(utils.KEY_LENGTH, '0123456789abcdef')
                cr.execute('''update res_users
                                set sso_key=%s
                                where id=%s''', (key, user_id.id))
            request.session.authenticate(db_name, login=login,
                                         password=key, uid=user_id.id)
        except http.AuthenticationError as e:
            raise
        except Exception as e:
            _logger.error("Error binding Http Remote User session",
                          exc_info=True)
            raise


randrange = random.SystemRandom().randrange


def randomString(length, chrs):
    """Produce a string of length random bytes, chosen from chrs."""
    n = len(chrs)
    return ''.join([chrs[randrange(n)] for _ in range(length)])
