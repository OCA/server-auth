# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, api, models, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    ldap_user_id = fields.Many2one(
        string='LDAP User',
        comodel_name='res.company.ldap.user',
    )

    @api.model
    def _get_ldap_sync_fields(self):
        return [
            'ldap_user_id',
            'login',
            'name',
            'email',
            'active',
        ]

    @api.multi
    def _ldap_sync_write_validate(self, vals):
        if self.filtered('ldap_user_id') and \
                not self.env.context.get('ldap_sync') and \
                any(f in self._get_ldap_sync_fields() for f in vals):
            raise UserError(_(
                'Modifying user synced from LDAP directory is not allowed'
            ))

    @api.multi
    def write(self, vals):
        self._ldap_sync_write_validate(vals)
        return super().write(vals)

    @api.multi
    def _ldap_sync_unlink_validate(self):
        if self.filtered('ldap_user_id') and \
                not self.env.context.get('ldap_sync'):
            raise UserError(_(
                'Deleting user synced from LDAP directory is not allowed'
            ))

    @api.multi
    def unlink(self):
        self._ldap_sync_unlink_validate()
        return super().unlink()

    @api.multi
    def unset_password(self):
        for user in self:
            self.env.cr.execute(
                'UPDATE res_users SET password=NULL WHERE id=%s',
                (user.id,)
            )
        self.invalidate_cache(['password'], self.ids)
