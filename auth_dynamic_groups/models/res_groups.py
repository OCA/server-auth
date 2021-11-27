# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


class ResGroups(models.Model):
    _inherit = "res.groups"

    is_dynamic = fields.Boolean("Dynamic")
    dynamic_group_condition = fields.Text(
        "Condition",
        help="The condition to be met for a user to be a "
        "member of this group. It is evaluated as python code at login "
        "time, you get `user` passed as a browse record",
    )

    def check_expression(
        self, expr, gd=None, ld=None, mode="eval", nocp=False, lb=False
    ):
        try:
            result = safe_eval(expr, gd, ld, mode, nocp, lb)
        except Exception as e:
            raise exceptions.UserError(_("Format: %s" % e))
        else:
            return result
        return False

    def eval_dynamic_group_condition(self, uid=None):
        user = self.env["res.users"].browse([uid]) if uid else self.env.user
        result = all(
            self.mapped(
                lambda this: self.check_expression(
                    this.dynamic_group_condition or "False",
                    {
                        "user": user.sudo(),
                        "any": any,
                        "all": all,
                        "filter": filter,
                    },
                )
            )
        )
        return result

    @api.constrains("dynamic_group_condition")
    def _check_dynamic_group_condition(self):
        try:
            self.filtered("is_dynamic").eval_dynamic_group_condition()
        except (NameError, SyntaxError, TypeError):
            raise exceptions.ValidationError(
                _("The condition doesn't evaluate correctly!")
            )

    def action_evaluate(self):
        res_users = self.env["res.users"]
        for user in res_users.search([]):
            res_users.update_dynamic_groups(user.id, self.env.cr.dbname)
