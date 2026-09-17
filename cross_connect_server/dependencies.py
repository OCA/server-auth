# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .models.cross_connect_client import CrossConnectClient


def authenticated_cross_connect_client() -> CrossConnectClient:
    pass
