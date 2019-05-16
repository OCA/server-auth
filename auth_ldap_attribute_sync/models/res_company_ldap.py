# Copyright (C) 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import fields, api, models, registry, tools, SUPERUSER_ID

_logger = logging.getLogger(__name__)

try:
    import ldap
    from ldap.filter import filter_format
except (ImportError) as err:
    _logger.debug(err)


class CompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'

    user_attributes_mapping = fields.One2many(
        string='User attributes mapping',
        comodel_name='ldap.attribute.mapping',
        inverse_name='ldap_id'
    )

    def _get_ldap_user(self, conf, login):
        entry = False
        try:
            filter = filter_format(conf['ldap_filter'], (login,))
        except TypeError:
            _logger.warning((
                'Could not format LDAP filter. '
                'Your filter should contain one \'%s\'.'
            ))
            return False
        try:
            results = self._query(conf, tools.ustr(filter))

            # Get rid of (None, attrs) for searchResultReference replies
            results = [i for i in results if i[0]]
            if len(results) == 1:
                entry = results[0]
        except ldap.LDAPError as e:
            _logger.error('An LDAP exception occurred: %s', e)
            raise e
        return entry

    def _map_attributes_to_fields(self, conf, ldap_entry, modes):
        SudoLdapAttributeMapping = self.env['ldap.attribute.mapping'].sudo()

        ldap_configuration = self.sudo().browse(conf['id'])

        fields = {}
        for mapping_id in ldap_configuration.user_attributes_mapping:
            mapping = SudoLdapAttributeMapping.browse(mapping_id.id)

            attribute = mapping.attribute_name
            field = mapping.field_name
            if not attribute or mapping.mode not in modes:
                _logger.info('Skipped field "%s"', field)
                continue

            try:
                fields[field] = ldap_entry[1][attribute][0].decode()
                _logger.info(
                    'Mapped field "%s" to LDAP attribute "%s"',
                    field,
                    attribute
                )
            except KeyError:
                _logger.warning('No LDAP attribute "%s" found', attribute)

        return fields

    def _map_ldap_attributes(self, conf, login, ldap_entry):
        fields = super()._map_ldap_attributes(
            conf,
            login,
            ldap_entry
        )

        _logger.info(
            'Initial setting field values from LDAP attributes for login "%s"',
            login
        )
        fields.update(self._map_attributes_to_fields(
            conf,
            ldap_entry,
            ['initial', 'always']
        ))

        return fields

    def _update_user(self, conf, user):
        if not user:
            ldap_entry = self._get_ldap_user(conf, self.env.user.login)
        else:
            ldap_entry = self._get_ldap_user(conf, user.login)
        if not ldap_entry:
            return ldap_entry

        _logger.info(
            'Updating field values from LDAP attributes for login "%s"',
            user.login
        )
        fields = self._map_attributes_to_fields(conf, ldap_entry, ['always'])

        with registry(self.env.cr.dbname).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            SudoUser = env['res.users'].sudo()
            SudoUser.browse(user.id).write(fields)
        return ldap_entry
