This module lets developpers add a new `jwt` authentication method on
Odoo controller routes.

To use it, you must:

- Create an `auth.jwt.validator` record to configure how the JWT token
  will be validated.
- Add an `auth="jwt_{validator-name}"` or
  `auth="public_or_jwt_{validator-name}"` attribute to the routes you
  want to protect where `{validator-name}` corresponds to the name
  attribute of the JWT validator record.

The `auth_jwt_demo` module provides examples.

The JWT validator can be configured with the following properties:

- `name`: the validator name, to match the `auth="jwt_{validator-name}"`
  route property.
- `audience`: a comma-separated list of allowed audiences, used to
  validate the `aud` claim.
- `issuer`: used to validate the `iss` claim.
- Signature type (secret or public key), algorithm, secret and JWK URI
  are used to validate the token signature.

In addition, the `exp` claim is validated to reject expired tokens.

If the `Authorization` HTTP header is missing, malformed, or contains an
invalid token, the request is rejected with a 401 (Unauthorized) code,
unless the cookie mode is enabled (see below).

If the token is valid, the request executes with the configured user id.
By default the user id selection strategy is `static` (i.e. the same for
all requests) and the selected user is configured on the JWT validator.
Additional strategies can be provided by overriding the `_get_uid()`
method and extending the `user_id_strategy` selection field.

The selected user is *not* stored in the session. It is only available
in `request.uid` (and thus it is the one used in `request.env`). To
avoid any confusion and mismatches between the bearer token and the
session, this module rejects requests made with an authenticated user
session.

Additionally, if a `partner_id_strategy` is configured, a partner is
searched and if found, its id is stored in the `request.jwt_partner_id`
attribute. If `partner_id_required` is set, a 401 (Unauthorized) is
returned if no partner was found. Otherwise `request.jwt_partner_id` is
left falsy. Additional strategies can be provided by overriding the
`_get_partner_id()` method and extending the `partner_id_strategy`
selection field.

The decoded JWT payload is stored in `request.jwt_payload`.

The `public_auth_jwt` method delegates authentication to the standard
Odoo `public` method when the Authorization header is not set. If it is
set, the regular JWT authentication is performed as described above.
This method is useful for public endpoints that need to work for
anonymous users, but can be enhanced when an authenticated user is know.
A typical use case is a "add to cart" endpoint that can work for
anonymous users, but can be enhanced by binding the cart to a known
customer when the authenticated user is known.

You can enable a cookie mode on JWT validators. In this case, the JWT
payload obtained from the `Authorization` header is returned as a
Http-Only cookie. This mode is sometimes simpler for front-end
applications which do not then need to store and protect the JWT token
across requests and can simply rely on the cookie management mechanisms
of browsers. When both the `Authorization` header and a cookie are
provided, the cookie is ignored in order to let clients authenticate
with a different user by providing a new JWT token.
