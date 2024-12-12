# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from secrets import token_urlsafe
from typing import Annotated, Callable, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from odoo import api, fields, models
from odoo.api import Environment

from odoo.addons.fastapi.dependencies import fastapi_endpoint, odoo_env

from ..dependencies import authenticated_cross_connect_client
from ..routers import cross_connect_router
from .cross_connect_client import CrossConnectClient


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app = fields.Selection(
        selection_add=[("cross_connect", "Cross Connect Endpoint")],
        ondelete={"cross_connect": "cascade"},
    )

    cross_connect_client_ids = fields.One2many(
        "cross.connect.client",
        "endpoint_id",
        string="Cross Connect Clients",
        help="The clients that can access this endpoint.",
    )
    cross_connect_allowed_group_ids = fields.Many2many(
        "res.groups",
        string="Cross Connect Allowed Groups",
        help="The groups that can access the cross connect clients of this endpoint.",
    )
    cross_connect_secret_key = fields.Char(
        help="The secret key used for cross connection.",
        required=True,
        default=lambda self: self._generate_secret_key(),
    )

    @api.model
    def _generate_secret_key(self):
        # generate random ~64 chars secret key
        return token_urlsafe(64)

    def _get_fastapi_routers(self) -> List[APIRouter]:
        routers = super()._get_fastapi_routers()

        if self.app == "cross_connect":
            routers += [cross_connect_router]

        return routers

    def _get_app_dependencies_overrides(self) -> Dict[Callable, Callable]:
        overrides = super()._get_app_dependencies_overrides()

        if self.app == "cross_connect":
            overrides[
                authenticated_cross_connect_client
            ] = api_key_based_authenticated_cross_connect_client

        return overrides

    def _get_routing_info(self):
        if self.app == "cross_connect":
            # Force to not save the HTTP session for the login to work correctly
            self.save_http_session = False
        return super()._get_routing_info()

    @property
    def _server_env_fields(self):
        return {"cross_connect_secret_key": {}}


def api_key_based_authenticated_cross_connect_client(
    api_key: Annotated[
        str,
        Depends(
            APIKeyHeader(
                name="api-key",
                description="Cross Connect Client API key.",
            )
        ),
    ],
    fastapi_endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    env: Annotated[Environment, Depends(odoo_env)],
) -> CrossConnectClient:
    cross_connect_client = (
        env["cross.connect.client"]
        .sudo()
        .search(
            [("api_key", "=", api_key), ("endpoint_id", "=", fastapi_endpoint.id)],
            limit=1,
        )
    )
    if not cross_connect_client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )
    return cross_connect_client
