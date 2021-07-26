CORS support is problematic in Odoo before 14.0.
This means the demo SPA in ``auth_jwt_demo`` does not work as is.
To make it work, you need to serve it from the same URL as Odoo,
or backport https://github.com/odoo/odoo/pull/56029.

This might also be worked around in ``auth_jwt`` by detecting
the cors preflight request and not requiring auth in that case.

This is left for future work, as my current focus is Odoo 14.0.
