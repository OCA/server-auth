By default, the trusted device cookies introduced by this module have a
``Secure`` flag. This decreases the likelihood of cookie theft via
eavesdropping but may result in cookies not being set by certain browsers
unless your Odoo instance uses HTTPS. If necessary, you can disable this flag
by going to ``Settings > Parameters > System Parameters`` and changing the
``auth_totp.secure_cookie`` key to ``0``.
