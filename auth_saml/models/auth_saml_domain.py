# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

class AuthSamlDomain(models.Model):
    """List of domains for SAML auto-provisioning"""
    _name = "auth.saml.domain"
    _description = "SAML2 domains in autoprovisioning"

    name = fields.Char("Domain Name", required=True)
