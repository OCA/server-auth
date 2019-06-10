# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class AuthSamlProviderOperator(models.AbstractModel):
    """Define operators for group mappings"""

    _name = "auth.saml.provider.operator"

    @api.model
    def operators(self):
        """Return names of function to call on this model as operator"""
        return ('contains', 'equals')

    def contains(self, attrs, mapping):
        matching_value = self.get_matching_value(attrs, mapping)
        return mapping.value in matching_value

    def equals(self, attrs, mapping):
        matching_value = self.get_matching_value(attrs, mapping)
        return mapping.value == matching_value

    @staticmethod
    def get_matching_value(attrs, mapping):
        matching_value = ''
        for k in attrs:
            if isinstance(k, tuple) and k[0] == mapping.saml_attribute:
                matching_value = attrs[k][0]
                break
        return matching_value
