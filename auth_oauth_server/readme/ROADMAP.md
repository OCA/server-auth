- Tokens are signed with a secret (HS256) known only to this database, so only
  Odoo itself can check them. Asymmetric keys published as a JWKS would let
  other servers check them too.
- No OpenID Connect (ID tokens, userinfo), no token introspection, no
  `private_key_jwt` client authentication.
- Redirect URIs must use https, or http on localhost: private-use schemes of
  native applications are not supported.
- Dynamic client registration is not rate limited; use a reverse proxy, or
  disable it.
- A resource created while Odoo runs registers its `auth="jwt_..."` route
  method only in the worker that created it (an `auth_jwt` limitation):
  restart the workers before using it in routes.
- Users of the portal can authorize applications when a resource allows their
  group, but cannot see or revoke them from the portal.
