# (c) 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import odoo
from odoo import http
from odoo.tools.func import lazy_property
from odoo.http import OpenERPSession, SessionExpiredException, request
from time import time


def post_load_hook():
    class RootUpdate(http.root.__class__):
        @lazy_property
        def session_store(self):
            store = super().session_store

            class OpenERPSessionUpdate(store.session_class):
                def check_security(self):
                    super().check_security()
                    env = odoo.api.Environment(
                        request.cr, self.uid, self.context)
                    delay = env['res.users']._auth_timeout_deadline_calculate()
                    if delay and self.update_time and self.update_time < delay:
                        self.logout(keep_db=True)
                        raise SessionExpiredException("Session expired")
                    ignored_urls = env[
                        'res.users'
                    ]._auth_timeout_get_ignored_urls()
                    if http.request.httprequest.path not in ignored_urls:
                        self.update_time = time()

                def _default_values(self):
                    super()._default_values()
                    self.setdefault("update_time", False)

                def authenticate(self, db, login=None, password=None,
                                 uid=None):
                    res = super().authenticate(
                        db, login=login, password=password, uid=uid)
                    if not self.update_time:
                        self.update_time = time()
                    return res

            store.session_class = OpenERPSessionUpdate
            return store

    http.root = RootUpdate()
