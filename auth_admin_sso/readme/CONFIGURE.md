## Idp-side

### Provider requirements
The OpenID Connect provider must:

| Feature | Description |
|---|---|
| **Discovery** | Publish `<issuer>/.well-known/openid-configuration` |
| **Public client** | Authorization code flow with PKCE, without client secret |
| **Redirect URI** | Accept `https://<instance>/auth_admin_sso/callback`, one per instance |
| **Signature** | Sign the ID token with `RS256` |
| **Roles claim** | Put the user's roles in an ID token claim (`roles` by default), as a list or a single string |

Known providers (only automated tests so far, no live test):

| Provider | Compatible | Note |
|---|---|---|
| **Microsoft Entra ID** | Yes | Roles in the `roles` claim |
| **Keycloak** | Yes | Public client; add a role mapper to the ID token, set `AUTH_ADMIN_SSO_ROLES_CLAIM` |
| **Okta** | Yes | Native app with PKCE; add a groups claim, set `AUTH_ADMIN_SSO_ROLES_CLAIM` |
| **Auth0** | Yes | Native app with PKCE; add roles with an Action, set `AUTH_ADMIN_SSO_ROLES_CLAIM` |
| **AWS Cognito** | Yes | App client without secret; set `AUTH_ADMIN_SSO_ROLES_CLAIM=cognito:groups` |
| **GitLab** | Yes | Non-confidential application; roles are GitLab groups, set `AUTH_ADMIN_SSO_ROLES_CLAIM=groups_direct` |
| **Google Workspace** | No | Requires a client secret, sends no roles |
| **GitHub** | No | Not OpenID Connect |

### Example IdP setup
Example with Microsoft Entra ID.
One app can serve all instances, but one app per customer is recommended.

1. Create an `App Registration`.
2. In `Authentication`, add the platform `Mobile and desktop applications`
   and add one redirect URI per instance:
   `https://<instance>/auth_admin_sso/callback`.
3. In `Authentication`, enable `Allow public client flows`.
4. In `App roles`, create one role per instance (e.g. `odoo-customer-a`).
5. In `Enterprise applications` > `Users and groups`:
   assign that role to the users or groups allowed on that instance.
   &rArr; they log in as the default login of the instance.
6. You can enforce the username through the role
   `odoo-customer-a.username.<username>`.
   It takes priority over `odoo-customer-a`.


## Odoo-side
On each Odoo instance, set these environment variables (or the same
names, lowercase, in the `[options]` section of the configuration file).

| Variable | Default Value | Required | Description |
|---|---|---|---|
| `AUTH_ADMIN_SSO_PROVIDER` | `oidc` | No | Provider implementation: `oidc`, or one added by another add-on |
| `AUTH_ADMIN_SSO_ISSUER` | | With `oidc` | Issuer URL, e.g. `https://login.microsoftonline.com/<tenant id>/v2.0` |
| `AUTH_ADMIN_SSO_CLIENT_ID` | | With `oidc` | Client id (Entra ID: app registration id) |
| `AUTH_ADMIN_SSO_REQUIRED_ROLE` | | Yes | Role of the instance, e.g. `odoo-customer-a`; prefix of the username roles |
| `AUTH_ADMIN_SSO_ROLES_CLAIM` | `roles` | No | ID token claim holding the roles |
| `AUTH_ADMIN_SSO_DEFAULT_LOGIN` | `admin` | No | Odoo login granted by the role of the instance |
| `AUTH_ADMIN_SSO_REDIRECT_LOGIN` | disabled | No | Enabled (`1`, `true`, `yes`) or disabled (any other value): `/web/login` with the default login and the redirect keyword goes to the SSO |
| `AUTH_ADMIN_SSO_REDIRECT_KEYWORD` | `sso` | No | Password triggering that redirect; not a secret, compared in plain text |
| `AUTH_ADMIN_SSO_CASE_INSENSITIVE_LOGIN` | disabled | No | Enabled (`1`, `true`, `yes`) or disabled (any other value): ignore case when comparing the login for that redirect |

`/auth_admin_sso/login` answers 404 while `AUTH_ADMIN_SSO_REQUIRED_ROLE`
is missing, or, with the `oidc` provider, `AUTH_ADMIN_SSO_ISSUER` or
`AUTH_ADMIN_SSO_CLIENT_ID`. An unknown provider answers 500.

### Design 

#### Why the instance sets the default login
Why the default Odoo login comes from the instance configuration and
not from the provider:

- Granting access and configuring the instance are done by different
  people.
  - The person granting access (e.g. a team manager) only assigns the
    role of the instance (e.g. `odoo-customer-a`), without knowing
    which Odoo user it maps to.
  - The person deploying the instance knows its Odoo users
    (e.g. the admin login may not be `admin`).

- When a specific Odoo login must be granted, the role
  `odoo-customer-a.username.<username>` does it without changing the
  instance configuration.


### Server-wide without installation
Load the module without installing it by adding it to the server wide
modules: `--load=base,web,auth_admin_sso` (or `server_wide_modules` in
the configuration file). Installing it in the database works too.
