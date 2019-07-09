# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,invalid-name
from odoo import _, api, fields, models

COUNT_RELATION_STATEMENT = """\
SELECT COUNT(*) AS kount
 FROM dynamic_group_relation_type_rel rel
 JOIN res_partner_relation_all AS rpra
   ON rel.type_selection_id = rpra.type_selection_id
 WHERE rel.gid = %(group_id)s
   AND (rpra.this_partner_id = %(partner_id)s OR rpra.other_partner_id = %(partner_id)s)
   AND (rpra.date_start IS NULL or rpra.date_start <= CURRENT_DATE)
   AND (rpra.date_end IS NULL or rpra.date_end >= CURRENT_DATE)
"""


class ResGroups(models.Model):
    _inherit = 'res.groups'

    dynamic_method_relation = fields.Selection(
        selection="_get_group_use_selection",
        string="Use partner relations",
        help="Include partners that have a specific type of relation")
    relation_type_ids = fields.Many2many(
        comodel_name='res.partner.relation.type.selection',
        relation='dynamic_group_relation_type_rel',
        column1='gid', column2='type_selection_id',
        string="Relation types that grant group membership",
        help="Specify the relations types that, if a user is connected"
             " with another partner through such a relation, grants the"
             "  user membership of this group.")
    allow_companies = fields.Boolean(
        help="Normally users should be persons, and therefore only the"
             " side of relations that apply to persons should be selectable.\n"
             "Allowing companies as users, will make all relations"
             " available for selection.")

    @api.onchange('allow_companies')
    def _onchange_allow_companies(self):
        self.ensure_one()
        relation_type_domain = [(1, '=', 1)]
        if not self.allow_companies:
            relation_type_domain = [
                '|',
                ('contact_type_this', '=', 'p'),
                ('contact_type_this', '=', False)]
        return {'domain': {'relation_type_ids': relation_type_domain}}

    @api.multi
    def dynamic_method_relation_check(self, user):
        """Check wether user has an active relation that gives group access."""
        self.ensure_one()
        self.env.cr.execute(
            COUNT_RELATION_STATEMENT,
            {
                'group_id': self.id,
                'partner_id': user.partner_id.id,
            }
        )
        kount = self.env.cr.fetchone()[0]
        message_parms = self._get_message_parms(user)
        message_parms['kount'] = kount
        self._debug_message(
            _("User %(user)s has %(kount)d relations qualifying"
              " for dynamic group %(group)s"),
            message_parms)
        return kount > 0
