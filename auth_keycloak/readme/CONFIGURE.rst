Settings -> Users & Companies -> OAuth Providers

In the `Users management (Keycloak)` section, fill in your user admin endpoint, this will be in
the form $keycloak_url/admin/realms/$realm/users. Also fill in the name of a keycloak user that
is allowed to create users, and its password.

This user must be allowed to query and manage users.
