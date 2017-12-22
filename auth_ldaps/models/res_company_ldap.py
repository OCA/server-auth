# Copyright (C) Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import ldap
from odoo import fields, models


class CompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'

    is_ssl = fields.Boolean(string='Use LDAPS', default=False)

    def get_ldap_dicts(self):
        res = super().get_ldap_dicts()
        for rec in res:
            ldap = self.sudo().browse(rec['id'])
            rec['is_ssl'] = ldap.is_ssl or False
        return res

    def connect(self, conf):
        if conf['is_ssl']:
            uri = 'ldaps://%s:%d' % (
                conf['ldap_server'], conf['ldap_server_port'])
            connection = ldap.initialize(uri)
            if conf['ldap_tls']:
                connection.start_tls_s()
            return connection
        return super().connect(conf)
