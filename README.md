
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/server-auth&target_branch=15.0)
[![Pre-commit Status](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml/badge.svg?branch=15.0)](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml?query=branch%3A15.0)
[![Build Status](https://github.com/OCA/server-auth/actions/workflows/test.yml/badge.svg?branch=15.0)](https://github.com/OCA/server-auth/actions/workflows/test.yml?query=branch%3A15.0)
[![codecov](https://codecov.io/gh/OCA/server-auth/branch/15.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-auth)
[![Translation Status](https://translation.odoo-community.org/widgets/server-auth-15-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-auth-15-0/?utm_source=widget)

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
[auth_admin_passkey](auth_admin_passkey/) | 15.0.1.0.0 |  | Allows system administrator to authenticate with any account
[auth_api_key](auth_api_key/) | 15.0.1.1.1 |  | Authenticate http requests from an API key
[auth_api_key_group](auth_api_key_group/) | 15.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Allow grouping API keys together. Grouping per se does nothing. This feature is supposed to be used by other modules to limit access to services or records based on groups of keys.
[auth_api_key_server_env](auth_api_key_server_env/) | 15.0.1.0.0 |  | Configure api keys via server env. This can be very useful to avoid mixing your keys between your various environments when restoring databases. All you have to do is to add a new section to your configuration file according to the following convention:
[auth_ldaps](auth_ldaps/) | 15.0.1.0.0 |  | Allows to use LDAP over SSL authentication
[auth_oauth_multi_token](auth_oauth_multi_token/) | 15.0.1.0.1 |  | Allow multiple connection with the same OAuth account
[auth_oidc](auth_oidc/) | 15.0.1.1.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Allow users to login through OpenID Connect Provider
[auth_saml](auth_saml/) | 15.0.1.4.4 | [![vincent-hatakeyama](https://github.com/vincent-hatakeyama.png?size=30px)](https://github.com/vincent-hatakeyama) | SAML2 Authentication
[auth_session_timeout](auth_session_timeout/) | 15.0.1.0.0 |  | This module disable all inactive sessions since a given delay
[auth_signup_partner_company](auth_signup_partner_company/) | 15.0.1.0.0 |  | Auth Signup Partner Company
[auth_signup_verify_email](auth_signup_verify_email/) | 15.0.1.0.0 |  | Force uninvited users to use a good email for signup
[auth_user_case_insensitive](auth_user_case_insensitive/) | 15.0.1.0.0 |  | Makes the user login field case insensitive
[password_security](password_security/) | 15.0.1.4.1 |  | Allow admin to set password security requirements.
[user_log_view](user_log_view/) | 15.0.1.0.0 | [![trojikman](https://github.com/trojikman.png?size=30px)](https://github.com/trojikman) | Allow to see user's actions log
[users_ldap_groups](users_ldap_groups/) | 15.0.1.0.1 |  | Adds user accounts to groups based on rules defined by the administrator.
[vault](vault/) | 15.0.2.1.0 |  | Password vault integration in Odoo
[vault_share](vault_share/) | 15.0.1.1.1 |  | Implementation of a mechanism to share secrets


Unported addons
---------------
addon | version | maintainers | summary
--- | --- | --- | ---
[auth_jwt](auth_jwt/) | 14.0.1.2.0 (unported) | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | JWT bearer token authentication.
[auth_jwt_demo](auth_jwt_demo/) | 14.0.1.2.0 (unported) | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Test/demo module for auth_jwt.

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
