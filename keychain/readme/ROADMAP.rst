- Account inheritence is not supported out-of-the-box (like defining common settings for all environments)
- Adapted to work with `server_environnement` modules
- Key expiration or rotation should be done manually
- Import passwords from data.xml

Security
========

This discussion: https://github.com/OCA/server-tools/pull/644 may help you decide if this module is suitable for your needs or not.

Common sense: Odoo is not a safe place for storing sensitive data.
But sometimes you don't have any other possibilities.
This module is designed to store credentials of data like carrier account, smtp, api keys...
but definitively not for credits cards number, medical records, etc.


By default, passwords are stored encrypted in the db using
symetric encryption `Fernet <https://cryptography.io/en/latest/fernet/>`_.
The encryption key is stored in openerp.tools.config.

Threats even with this module installed:

- unauthorized Odoo user want to access data: access is rejected by Odoo security rules
- authorized Odoo user try to access data with rpc api: he gets the passwords encrypted, he can't recover because the key and the decrypted password are not exposed through rpc
- db is stolen: without the key it's currently pretty hard to recover the passwords
- Odoo is compromised (malicious module or vulnerability): hacker has access to python and can do what he wants with Odoo: passwords of the current env can be easily decrypted
- server is compromised: idem

If your dev server is compromised, hacker can't decrypt your prod passwords
since you have different keys between dev and prod.

If you want something more secure: don't store any sensitive data in Odoo,
use an external system as a proxy, you can still use this module
for storing all other data related to your accounts.
