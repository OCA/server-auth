The Odoo 17.0 `mail_plugin` controller (`/mail_plugin/auth/access_token`)
creates its keys with `_generate(scope, name)`, without expiration date: a
non-administrator gets an error, and cannot connect the Outlook or Gmail
plugin.

Odoo 18.0 creates these keys in sudo, with an expiration date of
`mail_plugin.access_token_expiration_days` days (system parameter, default:
30). A glue module (e.g. `base_api_key_expiration_mail_plugin`, depending on
this module and `mail_plugin`, auto-installed) can do the same by overriding
`auth_access_token` and passing the date with the `api_key_expiration_date`
context key. The plugin keys would then expire, and their users reconnect the
plugin once expired.
