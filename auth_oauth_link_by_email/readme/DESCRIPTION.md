Odoo identifies an OAuth user by the provider and the subject it asserts,
stored as the user's OAuth User ID. Users that exist in Odoo before a
provider is configured are thus not recognized on their first login.

This module links them automatically: when an unknown subject logs in with a
verified email, it is linked to the existing user whose login is that
email. The
subject is then stored and used alone for subsequent logins, so later email
changes on either side do not matter.
