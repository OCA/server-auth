# Copyright 2026 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    _inherit = "res.users"

    def _get_mapped_roles(self, identity_payload):
        """Helper to evaluate the identity payload against role mappings."""
        roles_to_add = set()
        if not identity_payload:
            return roles_to_add

        cached_mappings = self.env["auth.user.role.mapping"]._get_all_mappings_cached()

        for mapping in cached_mappings:
            if mapping["attribute"] not in identity_payload:
                continue

            attribute_values = identity_payload.get(mapping["attribute"])
            if not isinstance(attribute_values, list):
                attribute_values = [attribute_values]

            for attr_val in attribute_values:
                attr_str = str(attr_val)
                if mapping["operator"] == "equals" and attr_str == mapping["value"]:
                    roles_to_add.add(mapping["role_id"])
                elif mapping["operator"] == "contains" and mapping["value"] in attr_str:
                    roles_to_add.add(mapping["role_id"])

        return roles_to_add

    def evaluate_and_apply_auth_roles(self, identity_payload, strict_sync=None):
        """
        Abstraction layer to evaluate an identity payload against global mappings
        and apply the resulting roles to the user.
        """
        self.ensure_one()

        # Fall back to global system parameter if not explicitly overridden
        if strict_sync is None:
            strict_sync = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("auth_user_role.strict_sync", "True")
                == "True"
            )

        roles_to_add = self._get_mapped_roles(identity_payload)

        existing_lines = self.role_line_ids
        existing_role_ids = set(existing_lines.mapped("role_id").ids)
        active_role_ids = set(self._get_enabled_roles().mapped("role_id").ids)

        commands = []
        roles_removed_log = []
        roles_added_log = []

        if strict_sync:
            roles_to_remove = existing_role_ids - roles_to_add
            if roles_to_remove:
                lines_to_remove = existing_lines.filtered(
                    lambda el: el.role_id.id in roles_to_remove
                )
                for line in lines_to_remove:
                    commands.append((2, line.id, 0))
                    roles_removed_log.append(line.role_id.name)

        for role_id in roles_to_add:
            if role_id not in existing_role_ids:
                commands.append((0, 0, {"role_id": role_id}))
                role = self.env["res.users.role"].browse(role_id)
                roles_added_log.append(role.name)
            elif role_id not in active_role_ids:
                line_to_activate = existing_lines.filtered(
                    lambda el, rid=role_id: el.role_id.id == rid
                )
                if line_to_activate:
                    commands.append((1, line_to_activate[0].id, {"date_to": False}))
                    role = self.env["res.users.role"].browse(role_id)
                    roles_added_log.append(f"{role.name} (Reactivated)")

        if commands:
            self.write({"role_line_ids": commands})
            if roles_removed_log:
                _logger.info(
                    "Identity Sync - Removed roles from user %s: %s",
                    self.login,
                    ", ".join(roles_removed_log),
                )
            if roles_added_log:
                _logger.info(
                    "Identity Sync - Granted roles to user %s: %s",
                    self.login,
                    ", ".join(roles_added_log),
                )

        if strict_sync:
            self.set_groups_from_roles(force=True)

        return list(roles_to_add)
