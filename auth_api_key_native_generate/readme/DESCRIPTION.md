This module adds an HTTP endpoint that allows to create a new native Odoo API key (`res.users.apikeys`) with a user's login and password.

It is for clients such as mobile apps that cannot use session-cookie
authentication and need a bearer API key to call the new native Odoo `/json/2` api.

The [`auth_api_key`](../auth_api_key) module manages its own `auth.api.key`
records and a custom `API-KEY` header. This module instead reuses the native
Odoo API key mechanism:

- Credentials are checked through `res.users.authenticate`, which goes through
  Odoo's `_assert_can_auth()` login cooldown for brute-force protection.
- Keys are created with `res.users.apikeys._generate()` using the `rpc` scope.
- Each key has a fixed validity window, 90 days by default and configurable.
