
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/server-auth&target_branch=17.0)
[![Pre-commit Status](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml/badge.svg?branch=17.0)](https://github.com/OCA/server-auth/actions/workflows/pre-commit.yml?query=branch%3A17.0)
[![Build Status](https://github.com/OCA/server-auth/actions/workflows/test.yml/badge.svg?branch=17.0)](https://github.com/OCA/server-auth/actions/workflows/test.yml?query=branch%3A17.0)
[![codecov](https://codecov.io/gh/OCA/server-auth/branch/17.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-auth)
[![Translation Status](https://translation.odoo-community.org/widgets/server-auth-17-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-auth-17-0/?utm_source=widget)

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
[auth_admin_passkey](auth_admin_passkey/) | 17.0.1.0.0 |  | Allows system administrator to authenticate with any account
[auth_api_key](auth_api_key/) | 17.0.1.0.0 |  | Authenticate http requests from an API key
[auth_api_key_server_env](auth_api_key_server_env/) | 17.0.1.0.0 |  | Configure api keys via server env. This can be very useful to avoid mixing your keys between your various environments when restoring databases. All you have to do is to add a new section to your configuration file according to the following convention:
[auth_oidc](auth_oidc/) | 17.0.1.0.0 | [![sbidoul](https://github.com/sbidoul.png?size=30px)](https://github.com/sbidoul) | Allow users to login through OpenID Connect Provider
[user_log_view](user_log_view/) | 17.0.1.0.0 | [![trojikman](https://github.com/trojikman.png?size=30px)](https://github.com/trojikman) | Allow to see user's actions log

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
