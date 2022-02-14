[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/251/15.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-server-auth-251)
[![Build Status](https://travis-ci.com/OCA/server-auth.svg?branch=15.0)](https://travis-ci.com/OCA/server-auth)
[![codecov](https://codecov.io/gh/OCA/server-auth/branch/15.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-auth)
[![Translation Status](https://translation.odoo-community.org/widgets/server-auth-15-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-auth-15-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# server-auth

TODO: add repo description.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[auth_api_key](auth_api_key/) | 15.0.1.0.0 |  | Authenticate http requests from an API key
[auth_api_key_group](auth_api_key_group/) | 15.0.1.0.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Allow grouping API keys together. Grouping per se does nothing. This feature is supposed to be used by other modules to limit access to services or records based on groups of keys.
[auth_api_key_server_env](auth_api_key_server_env/) | 15.0.1.0.0 |  | Configure api keys via server env. This can be very useful to avoid mixing your keys between your various environments when restoring databases. All you have to do is to add a new section to your configuration file according to the following convention:
[auth_saml](auth_saml/) | 15.0.1.0.0 |  | Saml2 Authentication


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

However, each module can have a totally different license, as long as they adhere to OCA
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----

OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
