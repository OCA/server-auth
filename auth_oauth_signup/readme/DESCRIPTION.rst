.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

Enable sign up for users logging in using OAuth2 on a per-provider basis, overriding the global setting.

Without this module, your options are:
 1. allow sign up for everyone who can access the login page
 2. import users (and provide values for `oauth_provider_id` and `oauth_uid`) before they log in for the first time.
