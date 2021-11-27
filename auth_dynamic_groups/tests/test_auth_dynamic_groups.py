# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import TransactionCase


class TestAuthDynamicGroups(TransactionCase):
    def test_auth_dynamic_groups(self):
        # without this, the below happens in another transaction we don't see
        self.env.registry.enter_test_mode(self.cr)
        env = self.env(cr=self.registry.cursor())
        demo_user = env.ref("base.user_demo")
        group = env["res.groups"].create(
            {
                "name": "dynamic group",
                "is_dynamic": True,
                "dynamic_group_condition": "'Demo' in user.name",
            }
        )
        group.action_evaluate()
        group.refresh()
        self.assertIn(demo_user, group.users)
        group.write({"users": [(6, False, [])]})
        self.assertFalse(group.users)
        self.env["res.users"]._login(self.env.cr.dbname, "demo", "demo", env)
        group.refresh()
        self.assertIn(demo_user, group.users)
        self.env.registry.leave_test_mode()
