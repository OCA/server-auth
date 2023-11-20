
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/server-auth&target_branch=13.0)
[![Pre-commit Status](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml/badge.svg?branch=13.0)](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml?query=branch%3A13.0)
[![Build Status](https://github.com/OCA/server-auth/actions/workflows/test.yml/badge.svg?branch=13.0)](https://github.com/OCA/server-auth/actions/workflows/test.yml?query=branch%3A13.0)
[![codecov](https://codecov.io/gh/OCA/server-auth/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-auth)
[![Translation Status](https://translation.odoo-community.org/widgets/server-auth-13-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-auth-13-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# server-auth

None

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[auth_api_key](auth_api_key/) | 13.0.1.1.1 |  | Authenticate http requests from an API key
[auth_from_http_remote_user](auth_from_http_remote_user/) | 13.0.1.0.0 |  | Authenticate via HTTP Remote User
[auth_jwt](auth_jwt/) | 13.0.1.1.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | JWT bearer token authentication.
[auth_jwt_demo](auth_jwt_demo/) | 13.0.1.1.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Test/demo module for auth_jwt.
[auth_ldaps](auth_ldaps/) | 13.0.1.0.2 |  | Allows to use LDAP over SSL authentication
[auth_oauth_autologin](auth_oauth_autologin/) | 13.0.1.0.2 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Automatically redirect to the OAuth provider for login
[auth_oauth_multi_token](auth_oauth_multi_token/) | 13.0.2.0.0 |  | Allow multiple connection with the same OAuth account
[auth_oidc](auth_oidc/) | 13.0.1.1.1 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Allow users to login through OpenID Connect Provider
[auth_saml](auth_saml/) | 13.0.1.0.1 |  | Saml2 Authentication
[auth_session_timeout](auth_session_timeout/) | 13.0.1.1.1 |  | This module disable all inactive sessions since a given delay
[auth_signup_verify_email](auth_signup_verify_email/) | 13.0.1.0.2 |  | Force uninvited users to use a good email for signup
[auth_user_case_insensitive](auth_user_case_insensitive/) | 13.0.1.0.0 |  | Makes the user login field case insensitive
[base_user_show_email](base_user_show_email/) | 13.0.1.0.0 |  | Untangle user login and email
[password_security](password_security/) | 13.0.1.0.0 |  | Allow admin to set password security requirements.
[users_ldap_groups](users_ldap_groups/) | 13.0.1.0.0 |  | Adds user accounts to groups based on rules defined by the administrator.
[users_ldap_mail](users_ldap_mail/) | 13.0.1.0.1 | [![joao-p-marques](https://github.com/joao-p-marques.png?size=30px)](https://github.com/joao-p-marques) | LDAP mapping for user name and e-mail
[users_ldap_populate](users_ldap_populate/) | 13.0.1.0.0 | [![joao-p-marques](https://github.com/joao-p-marques.png?size=30px)](https://github.com/joao-p-marques) | LDAP Populate
[vault](vault/) | 13.0.1.4.0 |  | Password vault integration in Odoo
[vault_share](vault_share/) | 13.0.1.0.1 |  | Implementation of a mechanism to share secrets

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
