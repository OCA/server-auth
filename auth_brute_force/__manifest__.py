{
    "name": "Authentication - Brute-Force Filter",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "summary": "Track Authentication Attempts and Prevent Brute-force Attacks",
    "author": "Nitrokey GmbH, GRAP, Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/system_parameters.xml",
        "views/res_authentication_attempt_views.xml",
    ],
    "installable": True,
}
