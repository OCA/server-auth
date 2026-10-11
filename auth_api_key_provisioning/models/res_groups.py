# Copyright 2026 Keboola
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class ResGroups(models.Model):
    _inherit = "res.groups"

    def write(self, vals):
        res = super().write(vals)
        # Privilege can be granted from the group side without ever calling
        # res.users.write: by adding members (``users``) or by making a group imply an
        # elevated one (``implied_ids``). The set of users affected by an implied_ids
        # change is transitive and awkward to compute exactly, so fall back to the full
        # sweep (narrowed to live-key holders, hence cheap). A pure ``users`` change
        # only affects the listed members, so re-check just those.
        if "implied_ids" in vals:
            self.env["res.users"]._apikey_provisioning_sweep_all()
        elif "users" in vals:
            users = self.mapped("users")
            if users:
                users._apikey_provisioning_revoke_if_unsafe()
        return res
