# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from contextlib import contextmanager

import psycopg2

from odoo import api, http, models, SUPERUSER_ID
from odoo.http import request


_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    _REMOTE_USER_ROLE = 'HTTP_USER_ROLES'
    _REMOTE_USER_ROLE_SEPARATOR = ','

    @classmethod
    def _authenticate(cls, auth_method='user'):
        auth_method = super()._authenticate(auth_method=auth_method)
        # if we reach this line, no exception was raised during auth so we are
        # logged in / granted anomymous
        if request.session.uid:
            cls._update_role_from_header()
        return auth_method

    @classmethod
    def _has_http_role_header(cls):
        headers = http.request.httprequest.headers.environ
        return cls._REMOTE_USER_ROLE in headers

    @classmethod
    def _get_http_role_header(cls):
        headers = http.request.httprequest.headers.environ
        return headers.get(cls._REMOTE_USER_ROLE, None)

    @classmethod
    def _get_http_role_codes(cls, header):
        """Return role codes from HTTP header.

        Return in a list the user role codes found in the HTTP
        header using the field and separator predefined.
        """
        roles = []
        if header:
            roles = header.split(cls._REMOTE_USER_ROLE_SEPARATOR)
        return roles

    @classmethod
    @contextmanager
    def _update_role_race_for_update(cls, user_id):
        """Lock the user and get an environment with a new Cursor

        If the roles changed, a race will start between all the requests,
        only one of them will be able to change the roles in DB.

        If we don't preemptively handle this case, they would be rollbacked
        and the requests unhandled. The first to acquire the lock will do it
        """
        with api.Environment.manage():
            with request.env.registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                try:
                    cr.execute(
                        "SELECT * FROM res_users WHERE id = %s "
                        "FOR UPDATE NOWAIT", (user_id,),
                        log_exceptions=False
                    )
                except psycopg2.OperationalError as e:
                    if e.pgcode == '55P03':
                        # Class 55: Object not in prerequisite state; 55P03:
                        # lock_not_available

                        # The Race was won by another request, let it do the
                        # job!
                        yield (False, env)
                    else:
                        # Unexpected OperationalError
                        raise
                else:
                    yield (True, env)

    @classmethod
    def _update_role_from_header(cls):
        """Update roles assigned to user.

        Read roles codes from the http header and compare with the actual roles
        of the logging user. If there is a difference, changes are applied.
        """
        if not cls._has_http_role_header():
            # if the header is not set at all in the request, we can
            # consider that we are in a trusted environment:
            # * the reverse proxy *must* set the header with the roles in any
            #   case
            # * when odoo requests itself for generating reports, it will
            #   not pass any header, we should not reset roles because of this
            # * it may be used for debugging an environment: direct access
            #   to odoo will not reset roles, access through the reverse proxy
            #   will pass the header. Never allow direct access to odoo besides
            #   a debugging use case though.
            return

        user = request.env['res.users'].browse(request.session.uid)
        roles_in_header = cls._get_http_role_header()
        if (not roles_in_header and not user.last_http_header_roles
                or roles_in_header == user.last_http_header_roles):
            return

        with cls._update_role_race_for_update(user.id) as (acquired, env):
            if not acquired:
                return
            _logger.debug(
                'user %s received header %s and previously had %s',
                user.id, roles_in_header, user.last_http_header_roles
            )

            user = user.with_env(env)
            new_roles = set()
            role_codes = cls._get_http_role_codes(roles_in_header)
            if role_codes:
                new_roles = set(env['res.users.role'].search(
                    [('user_role_code', 'in', role_codes)]).ids
                )
            env['res.users.role'].change_roles_remote_user(
                env, user.id, new_roles
            )
            user.last_http_header_roles = roles_in_header
