# Copyright 2026 Ivan Yelizariev <https://github.com/yelizariev>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Remove obsolete website-specific signup view copies."""


def migrate(cr, version):
    """Remove stale website-specific copies of the signup template.

    Older versions of Odoo may leave website-specific copies of
    ``auth_signup.signup`` in the database. These copies may contain an
    outdated architecture that does not include the login input expected
    by the inherited view provided by this module.

    When Odoo rebuilds website-specific views, the inherited view may fail
    validation against such an outdated copy.

    Delete only copies that:
    - are website-specific copies of ``auth_signup.signup``;
    - do not contain an input with ``name="login"``;
    - have no inherited views;
    - have no external IDs.

    This allows Odoo to recreate the website-specific view from the
    current template during the subsequent view initialization.
    """
    cr.execute(
        """
        DELETE FROM ir_ui_view AS v
        WHERE v.key = 'auth_signup.signup'
          AND v.website_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM jsonb_each_text(v.arch_db) AS lang(key, value)
              WHERE lang.value LIKE '%name="login"%'
          )
          AND NOT EXISTS (
              SELECT 1
              FROM ir_ui_view AS child
              WHERE child.inherit_id = v.id
          )
          AND NOT EXISTS (
              SELECT 1
              FROM ir_model_data AS d
              WHERE d.model = 'ir.ui.view'
                AND d.res_id = v.id
          )
        """
    )
