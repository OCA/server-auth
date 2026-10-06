# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    oauth_server_authorization_ids = fields.One2many(
        "oauth.server.authorization",
        "user_id",
        string="Connected Applications",
        domain=[("revoked", "=", False), ("code_used", "=", True)],
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["oauth_server_authorization_ids"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        # as for api_key_ids: the list sits in the preferences form, whose
        # save may send it back; the model refuses commands sent through sudo
        return super().SELF_WRITEABLE_FIELDS + ["oauth_server_authorization_ids"]
