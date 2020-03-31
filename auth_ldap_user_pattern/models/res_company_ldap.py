# Copyright (C) 2019 IBM Corp.
# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CompanyLDAP(models.Model):
    _inherit = "res.company.ldap"

    user_pattern = fields.Char(string="User Pattern", size=128)

    def map_ldap_attributes(self, conf, login, ldap_entry):
        res = super(CompanyLDAP, self).map_ldap_attributes(
            conf=conf, login=login, ldap_entry=ldap_entry
        )
        res.update({"is_ldap_user": True})
        return res

    def get_ldap_dicts(self):
        res = super(CompanyLDAP, self).get_ldap_dicts()
        for value in res:
            user_pattern = self.sudo().browse(value["id"]).user_pattern
            value.update({"user_pattern": user_pattern})
        return res
