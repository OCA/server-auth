This module requires you to configure two things :

#. The scopes are used to define restricted data access
#. The clients are used to declare applications that will be allowed to request tokens and data

To configure scopes, you need to:

#. Go to Settings > Users > OAuth Provider Scopes
#. Create some scopes:

 - The scope name and description will be displayed to the user on the authorization page.
 - The code is the value provided by the OAuth clients to request access to the scope.
 - The model defines which model the scope is linked to (access to user data, partners, sales orders, etc.).
 - The filter allows you to determine which records will be accessible through this scope. No filter means all records of the model are accessible.
 - The field names allows you to define which fields will be provided to the clients. An empty list only returns the id of accessible records.

To configure clients, you need to:

#. Go to Settings > Users > OAuth Provider Clients
#. Create at least one client:

 - The name will be displayed to the user on the authorization page.
 - The client identifier is the value provided by the OAuth clients to request authorizations/tokens.
 - The application type adapts the process to four pre-defined profiles:

   - Web Application : Authorization Code Grant
   - Mobile Application : Implicit Grant
   - Legacy Application : Resource Owner Password Credentials Grant
   - Backend Application : User Credentials Grant (not implemented yet)

 - The skip authorization checkbox allows the client to skip the authorization page, and directly deliver a token without prompting the user (useful when the application is trusted).
 - The allowed scopes list defines which data will be accessible by this client applicaton.
 - The allowed redirect URIs must match the URI sent by the client, to avoid redirecting users to an unauthorized service. The first value in the list is the default redirect URI.

For example, to configure an Odoo's *auth_oauth* module compatible client, you will enter these values :

- Name : Anything you want
- Client identifier : The identifier you want to give to this client
- Application Type : Mobile Application (Odoo uses the implicit grant mode, which corresponds to the mobile application profile)
- Allowed Scopes : Nothing required, but allowing access to current user's email and name is used by Odoo to fill user's information on signup
- Allowed Redirect URIs : http://odoo.example.com/auth_oauth/signin
