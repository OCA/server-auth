No configuration is required. The auto-link feature is active as soon as the
module is installed.

## How it works

When a user attempts to log in through an OAuth provider and no Odoo user is
found with a matching ``oauth_uid`` + ``oauth_provider_id``, this module will:

1. Extract the ``email`` claim from the OAuth token validation response.
2. Search for an active Odoo user whose ``login`` matches that email.
3. If found, write the ``oauth_provider_id``, ``oauth_uid``, and
   ``oauth_access_token`` onto that user record and return their login.
4. Subsequent logins will resolve directly via ``oauth_uid`` as usual.

If no matching user is found, or the email claim is absent, the standard
``auth_oauth`` flow continues (raising ``AccessDenied`` for unknown accounts).
