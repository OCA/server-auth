This module lets developpers add a new ``jwt`` authentication method on Odoo
controller routes.

To use it, you must:

* Create an ``auth.jwt.validator`` record to configure how the JWT token will
  be validated.
* Add an ``auth="jwt_{validator-name}"`` attribute to the routes
  you want to protect where ``{validator-name}`` corresponds to the name
  attribute of the JWT validator record.

The ``auth_jwt_demo`` module provides examples.

The JWT validator can be configured with the following properties:

* ``name``: the validator name, to match the ``auth="jwt_{validator-name}"``
  route property.
* ``audience``: a comma-separated list of allowed audiences, used to validate
  the ``aud`` claim.
* ``issuer``: used to validate the ``iss`` claim.
* Signature type (secret or public key), algorithm, secret and JWK URI
  are used to validate the token signature.

In addition, the ``exp`` claim is validated to reject expired tokens.

If the ``Authorization`` HTTP header is missing, malformed, or contains
an invalid token, the request is rejected with a 401 (Unauthorized) code.

If the token is valid, the request executes with the configured user id. By
default the user id selection strategy is ``static`` (i.e. the same for all
requests) and the selected user is configured on the JWT validator. Additional
strategies can be provided by overriding the ``_get_uid()`` method and
extending the ``user_id_strategy`` selection field.

The selected user is *not* stored in the session. It is only available in
``request.uid`` (and thus it is the one used in ``request.env``). To avoid any
confusion and mismatches between the bearer token and the session, this module
rejects requests made with an authenticated user session.

Additionally, if a ``partner_id_strategy`` is configured, a partner is searched
and if found, its id is stored in the ``request.jwt_partner_id`` attribute. If
``partner_id_required`` is set, a 401 (Unauthorized) is returned if no partner
was found. Otherwise ``request.jwt_partner_id`` is left falsy. Additional
strategies can be provided by overriding the ``_get_partner_id()`` method
and extending the ``partner_id_strategy`` selection field.

The decoded JWT payload is stored in ``request.jwt_payload``.
