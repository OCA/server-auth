# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Auth LDAP User Pattern",
    "version": "13.0.1.0.0",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "summary": "This module will support additional features for LDAP "
    "authentication based on user pattern",
    "category": "Authentication",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["auth_signup", "auth_ldap"],
    "data": [
        "security/security_view.xml",
        "views/res_company_ldap_view.xml",
        "views/res_users_view.xml",
    ],
    "installable": True,
    "maintainers": ["bodedra"],
}
