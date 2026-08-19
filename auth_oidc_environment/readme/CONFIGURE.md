To configure this module, you need to:

Create a module server_environment_file with a cfg file or set the
environment variable SERVER_ENV_CONFIG with the following section:

\[auth_oauth_provider.\<name\>\]

Where \<name\> is optional and must be equal to the name field you
defined in Odoo for the IDP.

Example of configuration

\[auth_oauth_provider.azure\]

client_id=... client_secret=...
