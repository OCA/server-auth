# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OAuth Provider",
    "summary": "Allows to use Odoo as an OAuth2 provider",
    "version": "14.0.1.0.0",
    "category": "Authentication",
    "website": "https://github.com/OCA/server-auth",
    "author": "SYLEAM, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "external_dependencies": {
        "python": ["oauthlib"],
    },
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "security/oauth_provider_security.xml",
        "security/ir.model.access.csv",
        "views/oauth_provider_client.xml",
        "views/oauth_provider_scope.xml",
        "templates/authorization.xml",
    ],
    "pre_init_hook": "pre_init_hook",
}
