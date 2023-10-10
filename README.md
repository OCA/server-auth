
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/server-auth&target_branch=16.0)
[![Pre-commit Status](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/OCA/server-auth/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/OCA/server-auth/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/OCA/server-auth/branch/16.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-auth)
[![Translation Status](https://translation.odoo-community.org/widgets/server-auth-16-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-auth-16-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Server Authentication

Modules for handling various authentication schemes

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[auth_admin_passkey](auth_admin_passkey/) | 16.0.1.0.0 |  | Allows system administrator to authenticate with any account
[auth_api_key](auth_api_key/) | 16.0.1.0.0 |  | Authenticate http requests from an API key
[auth_api_key_server_env](auth_api_key_server_env/) | 16.0.1.0.0 |  | Configure api keys via server env. This can be very useful to avoid mixing your keys between your various environments when restoring databases. All you have to do is to add a new section to your configuration file according to the following convention:
[auth_jwt](auth_jwt/) | 16.0.1.1.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | JWT bearer token authentication.
[auth_jwt_demo](auth_jwt_demo/) | 16.0.1.1.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Test/demo module for auth_jwt.
[auth_ldaps](auth_ldaps/) | 16.0.1.0.0 |  | Allows to use LDAP over SSL authentication
[auth_oidc](auth_oidc/) | 16.0.1.0.1 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Allow users to login through OpenID Connect Provider
[auth_oidc_environment](auth_oidc_environment/) | 16.0.1.0.0 |  | This module allows to use server env for OIDC configuration
[auth_saml](auth_saml/) | 16.0.1.0.2 | [![vincent-hatakeyama](https://github.com/vincent-hatakeyama.png?size=30px)](https://github.com/vincent-hatakeyama) | SAML2 Authentication
[auth_session_timeout](auth_session_timeout/) | 16.0.1.0.0 |  | This module disable all inactive sessions since a given delay
[auth_signup_verify_email](auth_signup_verify_email/) | 16.0.1.0.0 |  | Force uninvited users to use a good email for signup
[auth_user_case_insensitive](auth_user_case_insensitive/) | 16.0.1.0.0 |  | Makes the user login field case insensitive
[base_user_show_email](base_user_show_email/) | 16.0.1.0.0 |  | Untangle user login and email
[password_security](password_security/) | 16.0.1.0.0 |  | Allow admin to set password security requirements.
[user_log_view](user_log_view/) | 16.0.1.0.0 | [![trojikman](https://github.com/trojikman.png?size=30px)](https://github.com/trojikman) | Allow to see user's actions log
[users_ldap_groups](users_ldap_groups/) | 16.0.1.0.0 |  | Adds user accounts to groups based on rules defined by the administrator.
[users_ldap_mail](users_ldap_mail/) | 16.0.1.0.0 | [![joao-p-marques](https://github.com/joao-p-marques.png?size=30px)](https://github.com/joao-p-marques) | LDAP mapping for user name and e-mail
[users_ldap_populate](users_ldap_populate/) | 16.0.1.0.0 | [![joao-p-marques](https://github.com/joao-p-marques.png?size=30px)](https://github.com/joao-p-marques) | LDAP Populate

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
