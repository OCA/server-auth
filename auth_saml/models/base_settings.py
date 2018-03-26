# Copyright (C) 2010-2016 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


_SAML_UID_AND_PASS_SETTING = 'auth_saml.allow_saml.uid_and_internal_password'


class ResConfigSettings(models.TransientModel):
    """Inherit from res.config.settings to add a setting. This is only here
    for easier access; the setting is not actually stored by this (transient)
    collection. Instead, it is kept in sync with the
    "auth_saml.allow_saml.uid_and_internal_password" global setting. See
    comments in the definition of the "res.config.settings" collection for
    details.
    """

    _inherit = 'res.config.settings'

    allow_saml_uid_and_internal_password = fields.Boolean(
        string='Allow SAML users to posess an Odoo password '
               '(warning: decreases security)'
    )

    # take care to name the function with another name to not clash with column
    @api.model
    def allow_saml_and_password(self):
        """Read the allow_saml_uid_and_internal_password setting.
        Use the admin account to bypass security restrictions.
        """

        config_obj = self.env['ir.config_parameter']
        config_objs = config_obj.sudo().search(
            [('key', '=', _SAML_UID_AND_PASS_SETTING)], limit=1)

        # no configuration found reply with default value
        if len(config_objs) == 0:
            return False

        return (True if config_objs.value == '1' else False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(allow_saml_uid_and_internal_password=get_param(
            'auth_saml.allow_saml_uid_and_internal_password'))
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        if self.allow_saml_uid_and_internal_password:
            self.allow_saml_uid_and_internal_password = \
                self.allow_saml_and_password()
        set_param('auth_saml.allow_saml_uid_and_internal_password',
                  repr(self.allow_saml_uid_and_internal_password))
