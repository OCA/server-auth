# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response

from odoo.http import Dispatcher


def patch_dispatcher_pre_dispatch():
    """Patch odoo.http.Dispatcher's pre_dispatch method.

    For routes with cors enabled, Odoo will add a handler for the OPTIONS method,
    which will raise an abort HTTPException with a 204 response describing the allowed
    methods and headers in the Access-Control-* respnose headers.

    For routes with api_key authentication, we must inform the client that the
    API-KEY header is allowed.
    """
    original_pre_dispatch = Dispatcher.pre_dispatch

    def pre_dispatch(self, rule, args):
        get_header = self.request.future_response.headers.get
        set_header = self.request.future_response.headers.set
        routing = rule.endpoint.routing
        if (
            routing.get("cors")
            and routing.get("auth") == "api_key"
            and self.request.httprequest.method == "OPTIONS"
        ):
            try:
                return original_pre_dispatch(self, rule, args)
            except HTTPException as e:
                if (
                    isinstance(e.response, Response)
                    and e.response.status_code == 204
                    and get_header("Access-Control-Allow-Headers")
                ):
                    set_header(
                        "Access-Control-Allow-Headers",
                        f"{get_header('Access-Control-Allow-Headers')}, API-Key",
                    )
                raise
        else:
            return original_pre_dispatch(self, rule, args)

    Dispatcher.pre_dispatch = pre_dispatch
    Dispatcher.pre_dispatch._original_method = original_pre_dispatch


def post_load_hook():
    patch_dispatcher_pre_dispatch()
