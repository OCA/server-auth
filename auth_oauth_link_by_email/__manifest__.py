# Copyright 2026 spomata
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "OAuth - Link Existing Users by Verified Email",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "spomata, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "summary": "Link existing users to their OAuth subject on first login, "
    "by verified email",
    "depends": ["auth_oauth"],
    "data": ["views/auth_oauth_provider.xml", "views/res_users.xml"],
}
