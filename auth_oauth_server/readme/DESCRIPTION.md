This module makes Odoo an OAuth 2.1 authorization server: applications ask a
user for access, the user logs in on the usual Odoo login page and approves,
and the application receives tokens that let it call an API of Odoo as that
user, with that user's access rights.

It supports what the [MCP authorization
specification](https://modelcontextprotocol.io/specification/latest/basic/authorization)
requires, so MCP clients can connect to an MCP server hosted in Odoo:

- authorization code flow with mandatory PKCE (S256), and refresh tokens,
  rotated on each use;
- discovery: authorization server metadata (RFC 8414) and protected resource
  metadata (RFC 9728);
- applications may be registered by an administrator, register themselves
  (RFC 7591), or be identified by the URL of the details they publish
  (OAuth Client ID Metadata Documents);
- tokens bound to the API they were asked for (RFC 8707 resource indicators),
  `iss` in authorization responses (RFC 9207), token revocation (RFC 7009).

Access tokens are short-lived JWTs checked by an `auth_jwt` validator, which
the module creates for each protected API. Routes can therefore be protected
with `auth="jwt_<validator name>"`, as with any other `auth_jwt` validator.
Each token is also checked against the authorization it comes from, so that
revoking an authorization takes effect at once.

Logging in is left to Odoo: password, two-factor authentication, and login
through another provider (`auth_oauth`, `auth_oidc`, `auth_saml`) all work.
