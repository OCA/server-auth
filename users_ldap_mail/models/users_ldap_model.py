# Copyright Daniel Reis (https://launchpad.com/~dreis-pt)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields

import logging
_logger = logging.getLogger(__name__)


class CompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'

    name_attribute = fields.Char(
        'Name Attribute',
        default='cn',
        help="By default 'cn' is used. "
             "For ActiveDirectory you might use 'displayName' instead.",
    )
    mail_attribute = fields.Char(
        'E-mail attribute',
        default='mail',
        help="LDAP attribute to use to retrieve em-mail address.",
    )

    def _get_ldap_dicts(self):
        """
        Copy of auth_ldap's funtion, changing only the SQL, so that it returns
        all fields in the table.
        """
        return self.sudo().search([('ldap_server', '!=', False)],
                                  order='sequence').read([])

    def _map_ldap_attributes(self, conf, login, ldap_entry):
        values = super()._map_ldap_attributes(conf, login, ldap_entry)
        mapping = [
            ('name', 'name_attribute'),
            ('email', 'mail_attribute'),
        ]
        for value_key, conf_name in mapping:
            try:
                if conf[conf_name]:
                    values[value_key] = ldap_entry[1][conf[conf_name]][0]
            except KeyError:
                _logger.warning(
                    'No LDAP attribute "%s" found for login  "%s"' % (
                        conf.get(conf_name), values.get('login')))
        return values
