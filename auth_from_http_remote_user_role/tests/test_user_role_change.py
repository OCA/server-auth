# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase


class TestUserRoleChange(TransactionCase):

    def setUp(self):
        super().setUp()
        self.groupa = self.env['res.groups'].create({'name': 'group_a'})
        self.groupb = self.env['res.groups'].create({'name': 'group_b'})
        self.groupc = self.env['res.groups'].create({'name': 'group_c'})
        self.rolea = self.env['res.users.role'].create({
            'group_id': self.groupa.id,
            'user_role_code': 'code_A'
        })
        self.roleb = self.env['res.users.role'].create({
            'group_id': self.groupb.id,
            'user_role_code': 'code_B'
        })
        self.rolec = self.env['res.users.role'].create({
            'group_id': self.groupc.id,
            'user_role_code': 'code_C'
        })

    def test_update_user_role(self):
        u = self.env['res.users'].browse(1)
        new_roles = [self.rolea.id, self.roleb.id]
        self.env['res.users.role'].change_roles_remote_user(
            self.env, 1, new_roles)
        self.assertListEqual(u.role_ids.ids, new_roles)

        new_roles = [self.roleb.id, self.rolec.id]
        self.env['res.users.role'].change_roles_remote_user(
            self.env, 1, new_roles)
        self.assertListEqual(u.role_ids.ids, new_roles)

    def test_invalidate_last_http_header_on_role_edit(self):
        u = self.env['res.users'].browse(1)

        # Check that last_http_header_roles is reset each time it
        # has role changes

        # field groups_id edition on user
        u.last_http_header_roles = 'test'
        u.groups_id = False
        self.assertFalse(u.last_http_header_roles)

        u.last_http_header_roles = 'test'
        u.groups_id = self.env.ref("base.group_partner_manager")
        self.assertFalse(u.last_http_header_roles)

        # group unlink
        u.last_http_header_roles = 'test'
        u.groups_id.unlink()
        self.assertFalse(u.last_http_header_roles)

        # group write
        group = self.env.ref("base.group_no_one")
        u.last_http_header_roles = 'test'
        group.users |= u
        self.assertFalse(u.last_http_header_roles)

        # group create
        u.last_http_header_roles = 'test'
        group.copy()
        self.assertFalse(u.last_http_header_roles)

        # setting role_line_ids on user
        u.last_http_header_roles = 'test'
        triplets = [(0, False, {'role_id': self.rolea.id, 'user_id': u.id})]
        u.role_line_ids = triplets
        self.assertFalse(u.last_http_header_roles)

        # role line unlink
        u.last_http_header_roles = 'test'
        u.role_line_ids.unlink()
        self.assertFalse(u.last_http_header_roles)

        # role line create
        u.last_http_header_roles = 'test'
        self.env['res.users.role.line'].create({
            'user_id': u.id,
            'role_id': self.roleb.id,
        })
        self.assertFalse(u.last_http_header_roles)

        # role line change
        line = self.env['res.users.role.line'].create({
            'user_id': u.id,
            'role_id': self.roleb.id,
        })
        u.last_http_header_roles = 'test'
        line.role_id = self.rolec
        self.assertFalse(u.last_http_header_roles)
