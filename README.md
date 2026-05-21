
[![Support the OCA](https://odoo-community.org/readme-banner-image)](https://odoo-community.org/get-involved?utm_source=repo-readme)

# Server Authentication
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/server-auth&target_branch=16.0)
[![Pre-commit Status](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/OCA/server-auth/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/OCA/server-auth/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/OCA/server-auth/branch/16.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-auth)
[![Translation Status](https://translation.odoo-community.org/widgets/server-auth-16-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-auth-16-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

Modules for handling various authentication schemes

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[auth_admin_passkey](auth_admin_passkey/) | 16.0.1.0.0 |  | Allows system administrator to authenticate with any account
[auth_api_key](auth_api_key/) | 16.0.1.0.1 |  | Authenticate http requests from an API key
[auth_api_key_group](auth_api_key_group/) | 16.0.1.0.0 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Allow grouping API keys together. Grouping per se does nothing. This feature is supposed to be used by other modules to limit access to services or records based on groups of keys.
[auth_api_key_server_env](auth_api_key_server_env/) | 16.0.1.0.1 |  | Configure api keys via server env. This can be very useful to avoid mixing your keys between your various environments when restoring databases. All you have to do is to add a new section to your configuration file according to the following convention:
[auth_jwt](auth_jwt/) | 16.0.1.2.0 | <a href='https://github.com/sbidoul'><img src='https://github.com/sbidoul.png' width='32' height='32' style='border-radius:50%;' alt='sbidoul'/></a> | JWT bearer token authentication.
[auth_jwt_demo](auth_jwt_demo/) | 16.0.1.1.1 | <a href='https://github.com/sbidoul'><img src='https://github.com/sbidoul.png' width='32' height='32' style='border-radius:50%;' alt='sbidoul'/></a> | Test/demo module for auth_jwt.
[auth_jwt_server_env](auth_jwt_server_env/) | 16.0.1.0.0 |  | This addon adds auth.jwt.validator fields to server env
[auth_ldaps](auth_ldaps/) | 16.0.1.0.0 |  | Allows to use LDAP over SSL authentication
[auth_oauth_autologin](auth_oauth_autologin/) | 16.0.1.0.0 | <a href='https://github.com/sbidoul'><img src='https://github.com/sbidoul.png' width='32' height='32' style='border-radius:50%;' alt='sbidoul'/></a> | Automatically redirect to the OAuth provider for login
[auth_oauth_filter_by_domain](auth_oauth_filter_by_domain/) | 16.0.1.0.0 | <a href='https://github.com/natuan9'><img src='https://github.com/natuan9.png' width='32' height='32' style='border-radius:50%;' alt='natuan9'/></a> | Filter OAuth providers by domain
[auth_oauth_multi_token](auth_oauth_multi_token/) | 16.0.1.0.0 |  | Allow multiple connection with the same OAuth account
[auth_oauth_ropc](auth_oauth_ropc/) | 16.0.1.0.0 |  | Allow to login with OAuth Resource Owner Password Credentials Grant
[auth_oidc](auth_oidc/) | 16.0.1.4.0 | <a href='https://github.com/sbidoul'><img src='https://github.com/sbidoul.png' width='32' height='32' style='border-radius:50%;' alt='sbidoul'/></a> | Allow users to login through OpenID Connect Provider
[auth_oidc_environment](auth_oidc_environment/) | 16.0.1.0.0 |  | This module allows to use server env for OIDC configuration
[auth_saml](auth_saml/) | 16.0.1.2.1 | <a href='https://github.com/vincent-hatakeyama'><img src='https://github.com/vincent-hatakeyama.png' width='32' height='32' style='border-radius:50%;' alt='vincent-hatakeyama'/></a> | SAML2 Authentication
[auth_session_timeout](auth_session_timeout/) | 16.0.1.0.1 |  | This module disable all inactive sessions since a given delay
[auth_signup_verify_email](auth_signup_verify_email/) | 16.0.1.0.1 |  | Force uninvited users to use a good email for signup
[auth_user_case_insensitive](auth_user_case_insensitive/) | 16.0.1.0.0 |  | Makes the user login field case insensitive
[base_user_show_email](base_user_show_email/) | 16.0.1.0.0 |  | Untangle user login and email
[cross_connect_client](cross_connect_client/) | 16.0.1.1.0 | <a href='https://github.com/paradoxxxzero'><img src='https://github.com/paradoxxxzero.png' width='32' height='32' style='border-radius:50%;' alt='paradoxxxzero'/></a> | Cross Connect Client allows to connect to a Cross Connect Server enabled odoo instance.
[cross_connect_server](cross_connect_server/) | 16.0.1.1.0 | <a href='https://github.com/paradoxxxzero'><img src='https://github.com/paradoxxxzero.png' width='32' height='32' style='border-radius:50%;' alt='paradoxxxzero'/></a> | Cross Connect Server allows Cross Connect Client to connect to it.
[impersonate_login](impersonate_login/) | 16.0.1.0.1 | <a href='https://github.com/Kev-Roche'><img src='https://github.com/Kev-Roche.png' width='32' height='32' style='border-radius:50%;' alt='Kev-Roche'/></a> | tools
[password_security](password_security/) | 16.0.1.0.4 |  | Allow admin to set password security requirements.
[user_log_view](user_log_view/) | 16.0.1.0.0 | <a href='https://github.com/trojikman'><img src='https://github.com/trojikman.png' width='32' height='32' style='border-radius:50%;' alt='trojikman'/></a> | Allow to see user's actions log
[users_ldap_groups](users_ldap_groups/) | 16.0.1.0.1 |  | Adds user accounts to groups based on rules defined by the administrator.
[users_ldap_mail](users_ldap_mail/) | 16.0.1.0.0 | <a href='https://github.com/joao-p-marques'><img src='https://github.com/joao-p-marques.png' width='32' height='32' style='border-radius:50%;' alt='joao-p-marques'/></a> | LDAP mapping for user name and e-mail
[users_ldap_populate](users_ldap_populate/) | 16.0.1.0.2 | <a href='https://github.com/joao-p-marques'><img src='https://github.com/joao-p-marques.png' width='32' height='32' style='border-radius:50%;' alt='joao-p-marques'/></a> | LDAP Populate
[vault](vault/) | 16.0.1.0.3 |  | Password vault integration in Odoo
[vault_share](vault_share/) | 16.0.1.0.1 |  | Implementation of a mechanism to share secrets

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
