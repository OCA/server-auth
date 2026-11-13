# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import http
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestIrHttp(HttpCase):
    def test_session_with_inactive_language(self):
        """A logged-in session whose language is inactive still opens the backend

        A session stored without a context gets its language from
        Accept-Language, which may name an installed but inactive language.
        """
        self.assertFalse(self.env["res.lang"]._get_data(code="uk_UA"))
        session = self.authenticate("admin", "admin")
        session.context = {}
        http.root.session_store.save(session)
        # the language is only read while loading group definitions into a
        # cold cache, as on the first request of a freshly started worker
        self.registry.clear_cache("groups")

        response = self.url_open("/odoo", headers={"Accept-Language": "uk-UA,uk;q=0.9"})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("/web/login", response.url)
