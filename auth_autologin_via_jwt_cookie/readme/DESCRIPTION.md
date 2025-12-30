This module automatically authenticates Odoo users using a valid JWT
found in a shared browser cookie. If no Odoo session exists, the JWT is
verified via a JWKS endpoint, user information is retrieved from a
userinfo endpoint, and the matching user is logged in transparently
based on email.
