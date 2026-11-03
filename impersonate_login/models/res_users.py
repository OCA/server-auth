# Copyright 2024 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.http import request
from odoo.service import security

logger = logging.getLogger(__name__)


class Users(models.Model):
    _inherit = "res.users"

    impersonate_mode = fields.Selection(
        selection=[
            ("default", "Default"),
            ("allowed", "Allowed"),
            ("forbidden", "Forbidden"),
        ],
        string="Impersonation",
        default="default",
        required=True,
        groups="base.group_system",
        help="Default: follow the general setting (when 'Restrict Impersonation of "
        "Administration: Settings Users' is enabled, users with that access right "
        "cannot be impersonated).\n"
        "Allowed: this user can always be impersonated, even with that access right.\n"
        "Forbidden: this user can never be impersonated.",
    )

    impersonate_allowed = fields.Boolean(
        compute="_compute_impersonate_allowed",
        search="_search_impersonate_allowed",
        string="Can Be Impersonated",
        help="Whether the current user may switch to this user: never oneself, "
        "a user set to Forbidden, nor (when the general setting restricts "
        "them) a user with the 'Administration: Settings' access right.",
    )

    @api.depends("impersonate_mode", "groups_id")
    @api.depends_context("uid")
    def _compute_impersonate_allowed(self):
        for user in self:
            user.impersonate_allowed = (
                user.id != self.env.uid and not user._get_impersonation_refusal()
            )

    def _search_impersonate_allowed(self, operator, value):
        """Same rule as _get_impersonation_refusal(), as a SQL domain."""
        if operator not in ("=", "!=") or not isinstance(value, bool):
            raise UserError(self.env._("Operation not supported"))
        domain = [
            ("id", "!=", self.env.uid),
            ("impersonate_mode", "!=", "forbidden"),
        ]
        config_restrict = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("impersonate_login.restrict_impersonate_admin_settings")
        )
        if config_restrict:
            domain += [
                "|",
                ("impersonate_mode", "=", "allowed"),
                ("groups_id", "not in", self.env.ref("base.group_system").ids),
            ]
        # impersonate_mode is readable by administrators only: the subquery is
        # built as superuser, its result only says who may be switched to.
        query = self.sudo().with_context(active_test=False)._search(domain)
        allowed = (operator == "=") == value
        return [("id", "in" if allowed else "not in", query)]

    def _get_impersonation_refusal(self):
        """Why nobody may impersonate this user (a message), or False."""
        self.ensure_one()
        mode = self.sudo().impersonate_mode
        if mode == "forbidden":
            return self.env._("This user cannot be impersonated.")
        if mode == "allowed":
            return False
        config_restrict = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("impersonate_login.restrict_impersonate_admin_settings")
        )
        if config_restrict and self.env.ref("base.group_system") in (
            self.sudo().groups_id
        ):
            return self.env._(
                "You cannot impersonate users with"
                " 'Administration: Settings' access rights."
            )
        return False

    def _check_can_be_impersonated(self):
        """Raise if nobody may impersonate this user."""
        refusal = self._get_impersonation_refusal()
        if refusal:
            raise UserError(refusal)

    def _get_partner_name(self, user_id):
        return self.env["res.users"].browse(user_id).partner_id.name

    def _is_impersonate_user(self):
        self.ensure_one()
        return self.has_group("impersonate_login.group_impersonate_login")

    def impersonate_login(self):
        if request:
            if self.id != request.session.impersonate_from_uid:
                self._check_can_be_impersonated()
            if request.session.impersonate_from_uid:
                if self.id == request.session.impersonate_from_uid:
                    return self.back_to_origin_login()
                else:
                    raise UserError(_("You are already Logged as another user."))
            if self.id == request.session.uid:
                raise UserError(_("It's you."))
            if (
                request.env.user._is_impersonate_user()
                and request.env.user._is_internal()
            ):
                target_uid = self.id
                request.session.impersonate_from_uid = self._uid
                request.session.uid = target_uid
                impersonate_log = (
                    self.env["impersonate.log"]
                    .sudo()
                    .create(
                        {
                            "user_id": self._uid,
                            "impersonated_partner_id": self.env["res.users"]
                            .browse(target_uid)
                            .partner_id.id,
                            "date_start": fields.datetime.now(),
                        }
                    )
                )
                request.session.impersonate_log_id = impersonate_log.id
                logger.info(
                    f"IMPERSONATE: {self._get_partner_name(self._uid)} "
                    f"Login as {self._get_partner_name(self.id)}"
                )
                # invalidate session token cache as we've changed the uid
                request.env.registry.clear_cache()
                request.session.session_token = security.compute_session_token(
                    request.session, request.env
                )

                # reload the client; open the first available root menu
                menu = self.env["ir.ui.menu"].search([("parent_id", "=", False)])[:1]
                return {
                    "type": "ir.actions.client",
                    "tag": "reload",
                    "params": {"menu_id": menu.id},
                }

    @api.model
    def action_impersonate_login(self):
        if request:
            from_uid = request.session.impersonate_from_uid
            if not from_uid:
                action = self.env["ir.actions.act_window"]._for_xml_id(
                    "base.action_res_users"
                )
                action["views"] = [[self.env.ref("base.view_users_tree").id, "list"]]
                # Only the users that can be switched to: the others would only
                # show a button that ends in an error.
                action["domain"] = [
                    ("id", "!=", self.env.user.id),
                    ("share", "=", False),
                    ("impersonate_allowed", "=", True),
                ]
                action["target"] = "new"
                return action

    @api.model
    def back_to_origin_login(self):
        if request:
            from_uid = request.session.impersonate_from_uid
            if from_uid:
                request.session.uid = from_uid
                self.env["impersonate.log"].sudo().browse(
                    request.session.impersonate_log_id
                ).write(
                    {
                        "date_end": fields.datetime.now(),
                    }
                )
                # invalidate session token cache as we've changed the uid
                request.env.registry.clear_cache()
                request.session.impersonate_from_uid = False
                request.session.impersonate_log_id = False
                request.session.session_token = security.compute_session_token(
                    request.session, request.env
                )
                logger.info(
                    f"IMPERSONATE: {self._get_partner_name(from_uid)} "
                    f"Logout as {self._get_partner_name(self._uid)}"
                )

            # reload the client; open the first available root menu
            menu = self.env["ir.ui.menu"].search([("parent_id", "=", False)])[:1]
            return {
                "type": "ir.actions.client",
                "tag": "reload",
                "params": {"menu_id": menu.id},
            }
