# Copyright 2012-2018 Therp BV <https://therp.nl>
# Copyright 2018 Brainbean Apps <https://brainbeanapps.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
from logging import getLogger
from string import Template

from odoo import api, models

_logger = getLogger(__name__)


class ResCompanyLdapOperator(models.AbstractModel):
    """Define operators for group mappings"""

    _name = "res.company.ldap.operator"
    _description = "Definition op LDAP operations"

    @api.model
    def operators(self):
        """Return names (without '_') of function to call on this model as operator"""
        return ("contains", "equals", "query")

    def _contains(self, ldap_entry, mapping):
        return mapping.ldap_attribute in ldap_entry[1] and mapping.value in map(
            lambda x: x.decode(), ldap_entry[1][mapping.ldap_attribute]
        )

    def _equals(self, ldap_entry, mapping):
        return mapping.ldap_attribute in ldap_entry[1] and mapping.value == str(
            list(map(lambda x: x.decode(), ldap_entry[1][mapping.ldap_attribute]))
        )

    def _query(self, ldap_entry, mapping):
        query_string = Template(mapping.value).safe_substitute(
            {
                attr: self.safe_ldap_decode(ldap_entry[1][attr][0])
                for attr in ldap_entry[1]
            }
        )

        results = mapping.ldap_id._query(mapping.ldap_id.read()[0], query_string)
        _logger.debug('Performed LDAP query "%s" results: %s', query_string, results)

        return bool(results)

    def safe_ldap_decode(self, attr):
        """Safe LDAP decode; Base64 encode attributes containing binary data.
        Binary data can be stored in Active Directory, e.g., thumbnailPhoto is
        stored as binary. As Str.decoce() cannot handle binary, this method
        Base64 encodes the data in the attribute, instead, if decode fails.
        Using Base64 should be a suitable fallback, because the use cases of
        users_ldap_groups do not really require comparing binary attributes.
        """

        try:
            return attr.decode()
        except UnicodeDecodeError:
            return base64.b64encode(attr)
