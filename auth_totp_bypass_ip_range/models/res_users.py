# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import logging
from ipaddress import AddressValueError, IPv4Address, IPv4Network

from odoo import models
from odoo.http import request

_logger = logging.getLogger("auth_totp_bypass_ip_range")


class ResUsers(models.Model):
    _inherit = "res.users"

    def _auth_totp_bypass_ip_range(self):
        """
        Determine if the current request comes from an IP that bypasses MFA
        """
        networks = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("auth_totp_bypass_ip_range.networks", "")
            .split()
        )
        ip = IPv4Address(request.httprequest.environ["REMOTE_ADDR"])
        for network in networks:
            try:
                parsed_network = IPv4Network(network, strict=False)
            except AddressValueError:
                _logger.error("%s is not a valid network", network)
                continue
            if ip in parsed_network:
                return True
        return False

    def _mfa_type(self):
        """
        Don't do MFA if the request comes from an IP that is configured to bypass it
        """
        if self._auth_totp_bypass_ip_range():
            return None
        return super()._mfa_type()

    def _mfa_url(self):
        """
        Don't do MFA if the request comes from an IP that is configured to bypass it
        """
        if self._auth_totp_bypass_ip_range():
            return None
        return super()._mfa_url()
