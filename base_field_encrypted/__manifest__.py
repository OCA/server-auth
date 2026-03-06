{
    "name": "Base Field Encrypted",
    "summary": "Symmetric encryption for fields in Odoo using cryptography (Fernet)",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/generate_encryption_key_wizard_views.xml",
    ],
    "maintainers": ["antoniodavid"],
}
