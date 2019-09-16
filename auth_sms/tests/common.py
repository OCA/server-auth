# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from contextlib import contextmanager
from functools import partial
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request as WerkzeugRequest
from odoo import http
from odoo.tests.common import TransactionCase


class Common(TransactionCase):
    def setUp(self):
        super(Common, self).setUp()
        self.odoo_root = http.Root()
        self.session = self.odoo_root.session_store.new()
        self.env['res.users']._register_hook()
        self.demo_user = self.env.ref('auth_sms.demo_user')
        self.env['auth_sms.code'].search([]).unlink()

    @contextmanager
    def _request(self, path, method='POST', data=None):
        """yield request, endpoint for given http request data"""
        werkzeug_env = EnvironBuilder(
            method=method,
            path=path,
            data=data,
            headers=[('cookie', 'session_id=%s' % self.session.sid)],
            environ_base={
                'HTTP_HOST': 'localhost',
                'REMOTE_ADDR': '127.0.0.1',
            },
        ).get_environ()
        werkzeug_request = WerkzeugRequest(werkzeug_env)
        self.odoo_root.setup_session(werkzeug_request)
        werkzeug_request.session.db = self.env.cr.dbname
        self.odoo_root.setup_db(werkzeug_request)
        self.odoo_root.setup_lang(werkzeug_request)

        request = http.HttpRequest(werkzeug_request)
        request._env = self.env
        with request:
            routing_map = self.env['ir.http'].routing_map()
            endpoint, dummy = routing_map.bind_to_environ(werkzeug_env).match(
                return_rule=False,
            )
            yield request, partial(endpoint, **request.params)
