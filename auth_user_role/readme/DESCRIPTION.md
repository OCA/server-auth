This module provides a generic engine to map Identity Provider (IdP) attributes to Odoo user roles.
It acts as an abstraction layer built on top of the `base_user_role` module. 

By itself, this module does not handle authentication.
Instead, it is designed to be triggered by specialized "glue" modules (e.g., SAML, OAuth, LDAP) during the login process.
It evaluates incoming identity payloads against a set of configured global rules and dynamically provisions or revokes user roles.