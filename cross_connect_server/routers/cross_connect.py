# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from odoo import _, api
from odoo.exceptions import MissingError
from odoo.http import SESSION_LIFETIME, root

from odoo.addons.fastapi.dependencies import odoo_env

from ..dependencies import authenticated_cross_connect_client
from ..models.cross_connect_client import CrossConnectClient
from ..schemas import AccessRequest, AccessResponse, SyncResponse

cross_connect_router = APIRouter(tags=["Cross Connect"])


@cross_connect_router.get("/cross_connect/sync")
async def sync(
    cross_connect_client: Annotated[
        CrossConnectClient, Depends(authenticated_cross_connect_client)
    ],
) -> SyncResponse:
    """Send back to client sync information."""
    return SyncResponse.from_groups(cross_connect_client.group_ids)


@cross_connect_router.post("/cross_connect/access")
async def access(
    cross_connect_client: Annotated[
        CrossConnectClient, Depends(authenticated_cross_connect_client)
    ],
    access_request: AccessRequest,
) -> AccessResponse:
    """Send back to client a token."""
    return AccessResponse.from_params(
        client_id=cross_connect_client.id,
        token=cross_connect_client.sudo()._request_access(access_request),
    )


@cross_connect_router.get("/cross_connect/login/{client_id}/{token}")
async def login(
    client_id: int,
    token: str,
    env: Annotated[api.Environment, Depends(odoo_env)],
) -> RedirectResponse:
    """Log user and redirect to odoo index."""
    cross_connect_client = env["cross.connect.client"].sudo().browse(client_id)
    if not cross_connect_client:
        raise MissingError(_("Client not found"))
    user, redirect_url = cross_connect_client.sudo()._log_from_token(token)
    user = user.with_user(user)
    user._update_last_login()
    env = env(user=user.id)

    # Create a odoo session
    session = root.session_store.new()
    session.db = env.cr.dbname
    session.uid = user.id
    session.login = user.login
    session.context = dict(env["res.users"].context_get())
    session.session_token = user._compute_session_token(session.sid)
    root.session_store.save(session)
    # Redirect after login
    response = RedirectResponse(url=redirect_url)
    response.set_cookie(
        "session_id",
        session.sid,
        httponly=True,
        max_age=SESSION_LIFETIME,
    )
    return response
