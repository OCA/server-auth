# © 2019 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, models


class AuthSamlProviderOperator(models.AbstractModel):
    """Define operators for group mappings"""

    _name = "auth.saml.provider.operator"

    @api.model
    def operators(self):
        """Return names of function to call on this model as operator"""
        return ('contains', 'equals')

    def contains(self, attrs, mapping):
        matching_value = ''
        for k in attrs:
            if isinstance(k, tuple) and mapping.saml_attribute in k:
                for matching_value in attrs[k]:
                    if mapping.value in matching_value:
                        return True
        return False

    def equals(self, attrs, mapping):
        matching_value = ''
        for k in attrs:
            if isinstance(k, tuple) and mapping.saml_attribute in k:
                for matching_value in attrs[k]:
                    if mapping.value == matching_value:
                        return True
        return False
