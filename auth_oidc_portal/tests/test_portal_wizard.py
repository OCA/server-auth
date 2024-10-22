# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase, users


class TestPortalWizard(TransactionCase):
    def setUp(self):
        super(TestPortalWizard, self).setUp()

        self.partner = self.env["res.partner"].create(
            {
                "name": "Testing Partner",
                "email": "testing_partner@example.com",
            }
        )

    @users("admin")
    def test_portal_wizard_partner(self):
        portal_wizard = (
            self.env["portal.wizard"]
            .with_context(active_ids=[self.partner.id])
            .create({})
        )

        self.assertEqual(len(portal_wizard.user_ids), 1)

        portal_user = portal_wizard.user_ids
        portal_user.email = "first_email@example.com"

        oauth_provider_id = self.env["auth.oauth.provider"].search(
            [("enabled", "=", True)], limit=1
        )
        self.assertEqual(oauth_provider_id, portal_user.oauth_provider_id)

        portal_user.action_grant_access()
        new_user = portal_user.user_id

        self.assertEqual(new_user.oauth_uid, "first_email@example.com")
        self.assertEqual(new_user.oauth_provider_id, oauth_provider_id)
