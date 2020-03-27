After the installation of this module, you need to add some entries
in Odoo's config file: (etc/openerp.cfg)

> keychain_key = fyeMIx9XVPBBky5XZeLDxVc9dFKy7Uzas3AoyMarHPA=

You can generate keys with `python -c 'from cryptography.fernet import Fernet; print Fernet.generate_key()'`.

This key is used to encrypt account passwords.

If you plan to use environments, you should add a key per environment:

> keychain_key_dev = 8H_qFvwhxv6EeO9bZ8ww7BUymNt3xtQKYEq9rjAPtrc=

> keychain_key_prod = y5z-ETtXkVI_ADoFEZ5CHLvrNjwOPxsx-htSVbDbmRc=

keychain_key is used for encryption when no environment is set.
