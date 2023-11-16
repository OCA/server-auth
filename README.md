
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/server-auth&target_branch=12.0)
[![Pre-commit Status](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml/badge.svg?branch=12.0)](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml?query=branch%3A12.0)
[![Build Status](https://github.com/OCA/server-auth/actions/workflows/test.yml/badge.svg?branch=12.0)](https://github.com/OCA/server-auth/actions/workflows/test.yml?query=branch%3A12.0)
[![codecov](https://codecov.io/gh/OCA/server-auth/branch/12.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-auth)
[![Translation Status](https://translation.odoo-community.org/widgets/server-auth-12-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-auth-12-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Server Auth

Authentication related modules.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[auth_admin_passkey](auth_admin_passkey/) | 12.0.1.1.1 |  | Allows system administrator to authenticate with any account
[auth_api_key](auth_api_key/) | 12.0.3.0.1 |  | Authenticate http requests from an API key
[auth_api_key_environment](auth_api_key_environment/) | 12.0.2.0.0 |  | Use Server Environment for API Keys
[auth_from_http_remote_user](auth_from_http_remote_user/) | 12.0.1.0.0 |  | Authenticate via HTTP Remote User
[auth_ldap_attribute_sync](auth_ldap_attribute_sync/) | 12.0.1.0.0 |  | Allows to update users’ fields from LDAP attributes
[auth_ldaps](auth_ldaps/) | 12.0.1.0.1 |  | Allows to use LDAP over SSL authentication
[auth_oauth_multi_token](auth_oauth_multi_token/) | 12.0.1.0.1 |  | Allow multiple connection with the same OAuth account
[auth_oidc](auth_oidc/) | 12.0.1.2.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Allow users to login through OpenID Connect Provider
[auth_saml](auth_saml/) | 12.0.1.0.1 |  | Saml2 Authentication
[auth_session_timeout](auth_session_timeout/) | 12.0.1.0.2 |  | This module disable all inactive sessions since a given delay
[auth_signup_verify_email](auth_signup_verify_email/) | 12.0.1.0.3 |  | Force uninvited users to use a good email for signup
[auth_totp](auth_totp/) | 12.0.1.1.0 |  | Allows users to enable MFA and add optional trusted devices
[auth_totp_password_security](auth_totp_password_security/) | 12.0.1.0.0 |  | auth_totp and password_security compatibility
[auth_u2f](auth_u2f/) | 12.0.1.0.2 |  | 2nd factor authentication via U2F devices
[auth_user_case_insensitive](auth_user_case_insensitive/) | 12.0.1.0.0 |  | Makes the user login field case insensitive
[base_user_show_email](base_user_show_email/) | 12.0.1.0.0 |  | Untangle user login and email
[password_security](password_security/) | 12.0.1.1.4 |  | Allow admin to set password security requirements.
[user_log_view](user_log_view/) | 12.0.1.0.0 | [![trojikman](https://github.com/trojikman.png?size=30px)](https://github.com/trojikman) | Allow to see user's actions log
[users_ldap_groups](users_ldap_groups/) | 12.0.1.0.1 |  | Adds user accounts to groups based on rules defined by the administrator.
[users_ldap_mail](users_ldap_mail/) | 12.0.1.0.1 |  | LDAP mapping for user name and e-mail
[users_ldap_populate](users_ldap_populate/) | 12.0.1.0.2 |  | LDAP Populate

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
