# Copyright © 2025 XCG SAS
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import http


class Home(http.Controller):
    @http.route(
        "/web/logout_successful", type="http", auth="none", website=False, sitemap=False
    )
    def logout_successful(self):
        """Landing page after successful logout.
        Log out user if they were still logged in."""
        if http.request.session.uid:
            return http.request.redirect("/web/session/logout", 303)
        return http.request.render("auth_logout_redirect.logout_successful")
