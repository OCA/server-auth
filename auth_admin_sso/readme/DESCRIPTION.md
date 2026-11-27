Lets members of an organization log in as one shared Odoo user (`admin`
by default) with their own account at an OpenID Connect provider (e.g. Microsoft
Entra ID), instead of sharing its password.

- No button is added to the login page: the flow starts by opening
  `/auth_admin_sso/login` manually.
- `/web/login` keeps working as usual (e.g. to log in as a portal user).
- No configuration is stored in the database: everything comes from
  environment variables or the Odoo configuration file.
- No client secret is needed: the flow uses the authorization code flow
  with PKCE, as a public client.
- Access is granted per instance through a role given by the provider.
