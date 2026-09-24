Backport of [odoo/odoo#205500](https://github.com/odoo/odoo/pull/205500)
(Odoo 19.0): the system parameter `auth_totp.trusted_device_age` sets the
number of days a browser remembered on the two-factor authentication page
("Don't ask again on this device") is trusted. Odoo 17.0 hard-codes 90 days.

Like in Odoo 18.0+, the devices get an expiration date when they are created
(`base_api_key_expiration`), so a change of the parameter only applies to the
new devices. At the installation, the existing devices expire at their
creation date plus the parameter.

Like in Odoo 19.0, the `td_id` cookie of the browser lasts the parameter, and
the devices are no longer removed after 90 days: the autovacuum removes them
once expired (only the devices without expiration date keep the 90 days of
Odoo 17.0).

Uninstall this module when migrating to Odoo 19.0.
