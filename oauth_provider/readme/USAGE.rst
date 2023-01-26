This module will allow OAuth clients to use your Odoo instance as an OAuth provider.

Once configured, you must give these information to your client application :

#. Client identifier : Identifies the application (to be able to check allowed scopes and redirect URIs)
#. Allowed scopes : The codes of scopes allowed for this client
#. URLs for the requests :

  - Authorization request : http://odoo.example.com/oauth2/authorize
  - Token request : http://odoo.example.com/oauth2/token
  - Token information request : http://odoo.example.com/oauth2/tokeninfo
     Parameters : access_token
  - User information request : http://odoo.example.com/oauth2/userinfo
     Parameters : access_token
  - Any other model information request (depending on the scopes) : http://odoo.example.com/oauth2/otherinfo
     Parameters : access_token and model

For example, to configure the *auth_oauth* Odoo module as a client, you will enter these values :

- Provider name : Anything you want
- Client ID : The identifier of the client configured in your Odoo Provider instance
- Body : Text displayed on Odoo's login page link
- Authentication URL : http://odoo.example.com/oauth2/authorize
- Scope : A space separated list of scope codes allowed to the client in your Odoo Provider instance
- Validation URL : http://odoo.example.com/oauth2/tokeninfo
- Data URL : http://odoo.example.com/oauth2/userinfo
