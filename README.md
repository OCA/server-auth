
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/server-auth&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/server-auth/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/server-auth/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/OCA/server-auth/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-auth)
[![Translation Status](https://translation.odoo-community.org/widgets/server-auth-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-auth-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# server-auth

Odoo server side authentication modules

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[auth_admin_passkey](auth_admin_passkey/) | 14.0.1.0.1 |  | Allows system administrator to authenticate with any account
[auth_api_key](auth_api_key/) | 14.0.3.0.1 |  | Authenticate http requests from an API key
[auth_api_key_group](auth_api_key_group/) | 14.0.1.1.1 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Allow grouping API keys together. Grouping per se does nothing. This feature is supposed to be used by other modules to limit access to services or records based on groups of keys.
[auth_api_key_server_env](auth_api_key_server_env/) | 14.0.1.1.0 |  | Configure api keys via server env. This can be very useful to avoid mixing your keys between your various environments when restoring databases. All you have to do is to add a new section to your configuration file according to the following convention:
[auth_dynamic_groups](auth_dynamic_groups/) | 14.0.1.0.0 |  | Have membership conditions for certain groups
[auth_jwt](auth_jwt/) | 14.0.2.1.2 | <a href='https://github.com/sbidoul'><img src='https://github.com/sbidoul.png' width='32' height='32' style='border-radius:50%;' alt='sbidoul'/></a> | JWT bearer token authentication.
[auth_jwt_demo](auth_jwt_demo/) | 14.0.1.3.0 | <a href='https://github.com/sbidoul'><img src='https://github.com/sbidoul.png' width='32' height='32' style='border-radius:50%;' alt='sbidoul'/></a> | Test/demo module for auth_jwt.
[auth_ldaps](auth_ldaps/) | 14.0.1.0.1 |  | Allows to use LDAP over SSL authentication
[auth_oauth_autologin](auth_oauth_autologin/) | 14.0.1.0.1 | <a href='https://github.com/sbidoul'><img src='https://github.com/sbidoul.png' width='32' height='32' style='border-radius:50%;' alt='sbidoul'/></a> | Automatically redirect to the OAuth provider for login
[auth_oauth_multi_token](auth_oauth_multi_token/) | 14.0.1.0.0 |  | Allow multiple connection with the same OAuth account
[auth_oidc](auth_oidc/) | 14.0.1.2.0 | <a href='https://github.com/sbidoul'><img src='https://github.com/sbidoul.png' width='32' height='32' style='border-radius:50%;' alt='sbidoul'/></a> | Allow users to login through OpenID Connect Provider
[auth_oidc_environment](auth_oidc_environment/) | 14.0.1.0.1 |  | This module allows to use server env for OIDC configuration
[auth_saml](auth_saml/) | 14.0.1.2.2 |  | SAML2 Authentication
[auth_session_timeout](auth_session_timeout/) | 14.0.1.0.2 |  | This module disable all inactive sessions since a given delay
[auth_signup_verify_email](auth_signup_verify_email/) | 14.0.1.0.1 |  | Force uninvited users to use a good email for signup
[auth_user_case_insensitive](auth_user_case_insensitive/) | 14.0.1.0.1 |  | Makes the user login field case insensitive
[base_user_empty_password](base_user_empty_password/) | 14.0.1.0.0 | <a href='https://github.com/grindtildeath'><img src='https://github.com/grindtildeath.png' width='32' height='32' style='border-radius:50%;' alt='grindtildeath'/></a> | Allows to empty password of users
[base_user_show_email](base_user_show_email/) | 14.0.1.0.0 |  | Untangle user login and email
[impersonate_login](impersonate_login/) | 14.0.1.0.1 | <a href='https://github.com/Kev-Roche'><img src='https://github.com/Kev-Roche.png' width='32' height='32' style='border-radius:50%;' alt='Kev-Roche'/></a> | tools
[password_security](password_security/) | 14.0.1.1.0 |  | Allow admin to set password security requirements.
[user_log_view](user_log_view/) | 14.0.1.0.0 | <a href='https://github.com/trojikman'><img src='https://github.com/trojikman.png' width='32' height='32' style='border-radius:50%;' alt='trojikman'/></a> | Allow to see user's actions log
[users_ldap_groups](users_ldap_groups/) | 14.0.1.0.1 |  | Adds user accounts to groups based on rules defined by the administrator.
[users_ldap_mail](users_ldap_mail/) | 14.0.1.0.1 | <a href='https://github.com/joao-p-marques'><img src='https://github.com/joao-p-marques.png' width='32' height='32' style='border-radius:50%;' alt='joao-p-marques'/></a> | LDAP mapping for user name and e-mail
[users_ldap_populate](users_ldap_populate/) | 14.0.1.0.0 | <a href='https://github.com/joao-p-marques'><img src='https://github.com/joao-p-marques.png' width='32' height='32' style='border-radius:50%;' alt='joao-p-marques'/></a> | LDAP Populate
[vault](vault/) | 14.0.1.9.0 |  | Password vault integration in Odoo
[vault_share](vault_share/) | 14.0.1.2.1 |  | Implementation of a mechanism to share secrets

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
