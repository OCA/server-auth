# © 2019 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AuthSamlProviderGroupMapping(models.Model):
    _name = 'auth.saml.provider.group_mapping'
    _description = 'SAML group mapping'
    _rec_name = 'saml_attribute'
    _order = 'saml_attribute'

    saml_id = fields.Many2one(
        'auth.saml.provider',
        'SAML Provider',
        required=True,
        ondelete='cascade',
    )
    saml_attribute = fields.Char(
        'SAML attribute',
        help=(
            'The SAML attribute to check.\n'
        )
    )
    operator = fields.Selection(
        lambda self: [
            (o, o) for o in self.env['auth.saml.provider.operator'].operators()
        ],
        'Operator',
        help=(
            'The operator to check the attribute against the value\n'
        ),
        default='equals',
        required=True
    )
    value = fields.Char(
        'Value',
        help=(
            'The value to check the attribute against.\n'
        ),
        required=True
    )
    group_id = fields.Many2one(
        'res.groups',
        'Odoo group',
        help='The Odoo group to assign',
        required=True
    )
