# Copyright (C) 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)

try:
    import ldap
except (ImportError) as err:
    _logger.debug(err)


class CompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'
    _description = 'Company LDAP configuration'

    name_attribute = fields.Char(string='Name attribute', default='cn')
    name_attribute_mode = fields.Selection(
        string='Name attribute sync mode',
        selection='_attribute_modes',
        default='initial'
    )

    email_attribute = fields.Char(string='Email attribute', default='mail')
    email_attribute_mode = fields.Selection(
        string='Email attribute sync mode',
        selection='_attribute_modes',
        default='initial'
    )

    phone_attribute = fields.Char(string='Phone attribute')
    phone_attribute_mode = fields.Selection(
        string='Phone attribute sync mode',
        selection='_attribute_modes'
    )

    mobile_attribute = fields.Char(string='Mobile attribute')
    mobile_attribute_mode = fields.Selection(
        string='Mobile attribute sync mode',
        selection='_attribute_modes'
    )

    function_attribute = fields.Char(string='Jon Position attribute')
    function_attribute_mode = fields.Selection(
        string='Jon Position attribute sync mode',
        selection='_attribute_modes'
    )

    def _fields_to_sync(self):
        return [
            'name',
            'email',
            'phone',
            'mobile',
            'function'
        ]

    def _attribute_modes(self):
        return [
            ('initial', 'On user creation'),
            ('always', 'On every login')
        ]

    def _get_ldap_dicts(self):
        res = super()._get_ldap_dicts()
        for rec in res:
            ldap = self.sudo().browse(rec['id'])
            for field in self._fields_to_sync():
                rec['%s_attribute' % field] = getattr(
                    ldap,
                    '%s_attribute' % field
                )
                rec['%s_attribute_mode' % field] = getattr(
                    ldap,
                    '%s_attribute_mode' % field
                )
        return res

    def _map_ldap_attributes(self, conf, login, ldap_entry):
        fields = super(CompanyLDAP, self)._map_ldap_attributes(
            conf,
            login,
            ldap_entry
        )

        for field in self._fields_to_sync():
            attribute = conf['%s_attribute' % field]
            mode = conf['%s_attribute_mode' % field]
            if not attribute or not mode:
                continue

            try:
                fields[field] = ldap_entry[1][attribute][0]
            except KeyError:
                _logger.warning(
                    'No LDAP attribute "%s" found for login  "%s"' % (
                        attribute,
                        login
                    )
                )

        return fields

    def _authenticate(self, conf, login, password):
        ldap_entry = super(CompanyLDAP, self)._authenticate(
            conf,
            login,
            password
        )

        if not self.env.user:
            return ldap_entry

        user = self.env['res.users'].sudo().browse(self.env.user.id)
        for field in self._fields_to_sync():
            attribute = conf['%s_attribute' % field]
            mode = conf['%s_attribute_mode' % field]
            if not attribute or mode != 'always':
                continue

            try:
                setattr(user, field, ldap_entry[1][attribute][0])
            except KeyError:
                _logger.warning(
                    'No LDAP attribute "%s" found for login  "%s"' % (
                        attribute,
                        login
                    )
                )

        return ldap_entry
