Backport of [odoo/odoo#178558](https://github.com/odoo/odoo/pull/178558)
(Odoo 18.0), with its follow-up fix
[odoo/odoo@3b3ee6bb5f](https://github.com/odoo/odoo/commit/3b3ee6bb5f):
API keys get an expiration date, set when they are created.

- The maximum duration of a key depends on the groups of its user (90 days
  for internal users). Only administrators can create persistent keys.
- An expired key is refused, and deleted by the autovacuum.
- The keys existing at the installation are persistent.

Differences with Odoo 18.0:

- `_generate` has no `expiration_date` parameter, because the Odoo 17.0
  overrides only take `scope` and `name`: the date is given with the
  `api_key_expiration_date` context key, and is stored on the key after its
  creation. Without it, a non-administrator gets an error: unlike 18.0,
  the `mail_plugin` controller is not adapted (see the roadmap). The expiration date is not
  required for the `auth_totp` trusted devices, whose 17.0 controller passes
  none: they are removed after 90 days by `_gc_device`, unless the
  `auth_totp_trusted_device_age` module (OCA/server-auth#1014) gives them an
  expiration date.
- The portal form ([odoo/odoo@bf554a1761](https://github.com/odoo/odoo/commit/bf554a1761))
  is not backported: keys created from the portal expire after 1 day.

When migrating to Odoo 18.0, merge this module into `base` (e.g. with
`merge_modules` of OpenUpgrade): uninstalling it would drop the expiration
date of the keys.
