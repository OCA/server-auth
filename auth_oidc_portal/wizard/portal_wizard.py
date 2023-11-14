from odoo import fields, models
from odoo.tools import email_normalize


class PortalWizardUser(models.TransientModel):
    # A model to configure users in the portal wizard.

    _inherit = "portal.wizard.user"

    def _get_default_provider(self):
        return self.env["auth.oauth.provider"].search([("enabled", "=", True)], limit=1)

    oauth_provider_id = fields.Many2one(
        "auth.oauth.provider",
        string="OAuth Provider",
        default=_get_default_provider,
        domain=[("enabled", "=", True)],
    )

    def _create_user(self):
        # create a new user for wizard_user.partner_id
        # :returns record of res.users

        user = super(PortalWizardUser, self)._create_user()
        if self.oauth_provider_id:
            user.oauth_uid = email_normalize(self.email)
            user.oauth_provider_id = self.oauth_provider_id

        return user
