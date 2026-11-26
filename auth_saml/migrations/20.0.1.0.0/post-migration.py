# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Font Awesome is no longer available in Odoo 20.0. Replace the old default
# icon class of the login button by the new default one. Custom values are
# kept as they are.

OLD_CSS_CLASS = "fa fa-fw fa-sign-in text-primary"
NEW_CSS_CLASS = "oi oi-fw text-primary"


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        "UPDATE auth_saml_provider SET css_class = %s WHERE css_class = %s",
        (NEW_CSS_CLASS, OLD_CSS_CLASS),
    )
