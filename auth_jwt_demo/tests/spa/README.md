# auth_jwt demo app

Inspired by https://auth0.com/docs/quickstart/spa/vanillajs, using
https://github.com/IdentityModel/oidc-client-js.

First start keycloak with `keycloak.sh` in `../keycloak`. Then serve this app by running
`python3 -m http.server` in this directory.

Try `demo/demo` as keycloak login.

The `Who am I ?` button calls the `http://localhost:8069/auth_jwt_demo/keycloak/whoami`
Odoo endpoint which is provided by this `auth_jwt_demo` module.
