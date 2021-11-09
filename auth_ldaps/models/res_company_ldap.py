# Copyright (C) Creu Blanca
# Copyright (C) 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import logging

import ldap

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CompanyLDAP(models.Model):
    _inherit = "res.company.ldap"
    _description = "Company LDAP configuration"

    is_ssl = fields.Boolean(string="Use LDAPS", default=False)
    skip_cert_validation = fields.Boolean(
        string="Skip certificate validation", default=False
    )

    def _get_ldap_dicts(self):
        res = super()._get_ldap_dicts()
        for rec in res:
            ldap = self.sudo().browse(rec["id"])
            rec["is_ssl"] = ldap.is_ssl or False
            rec["skip_cert_validation"] = ldap.skip_cert_validation or False
        return res

    def _connect(self, conf):
        if conf["is_ssl"]:
            uri = "ldaps://%s:%d" % (conf["ldap_server"], conf["ldap_server_port"])
            connection = ldap.initialize(uri)
            if conf["skip_cert_validation"]:
                connection.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)
                # this creates a new tls context, which is required to apply
                # the options, but it also clears the default options defined
                # in the openldap's configuration file, such as the TLS_CACERT
                # option, which specifies the file containing the trusted
                # certificates. this causes certificate verification to fail,
                # even if it would succeed with the default options. this is
                # why this is only called if we want to skip certificate
                # verification.
                connection.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
            if conf["ldap_tls"]:
                connection.start_tls_s()
            return connection
        return super()._connect(conf)
