When installed, this module automatically links existing Odoo users to an
OAuth provider on their first login, by matching the email address from the
OAuth token with the user's login (which is their email in Odoo).

This is useful when users already exist in Odoo (created manually or imported)
and you want them to authenticate via an OAuth provider without having to
recreate their accounts.
