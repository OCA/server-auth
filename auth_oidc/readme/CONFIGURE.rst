Setup for Microsoft Azure
~~~~~~~~~~~~~~~~~~~~~~~~~

Example configuration with OpenID Connect implicit flow.
This configuration is not recommended because it exposes the access token
to the client, and in logs.

1. configure a new web application in Azure with OpenID and implicit flow (see
   the `provider documentation
   <https://docs.microsoft.com/en-us/powerapps/maker/portals/configure/configure-openid-provider)>`_)
2. in this application the redirect url must be be "<url of your
   server>/auth_oauth/signin" and of course this URL should be reachable from
   Azure
3. create a new authentication provider in Odoo with the following
   parameters (see the `portal documentation
   <https://docs.microsoft.com/en-us/powerapps/maker/portals/configure/configure-openid-settings>`_
   for more information):

* Provider Name: Azure
* Auth Flow: OpenID Connect
* Client ID: use the value of the OAuth2 autorization endoing (v2) from the Azure Endpoints list
* Body: Azure SSO
* Authentication URL: use the value of "OAuth2 autorization endpoint (v2)" from the Azure endpoints list
* Scope: openid email
* Validation URL: use the value of "OAuth2 token endpoint (v2)" from the Azure endpoints list
* Allowed: yes


Setup for Keycloak
~~~~~~~~~~~~~~~~~~

Example configuration with OpenID Connect authorization code flow.

In Keycloak:

1. configure a new Client
2. make sure Authorization Code Flow is Enabled.
3. configure the client Access Type as "confidential" and take note of the client secret in the Credentials tab
4. configure the redirect url to be "<url of your server>/auth_oauth/signin"

In Odoo, create a new Oauth Provider with the following parameters:

* Provider name: Keycloak (or any name you like that identify your keycloak
  provider)
* Auth Flow: OpenID Connect (authorization code flow)
* Client ID: the same Client ID you entered when configuring the client in Keycloak
* Client Secret: found in keycloak on the client Credentials tab
* Allowed: yes
* Body: the link text to appear on the login page, such as Login with Keycloak
* Scope: openid email
* Authentication URL: The "authorization_endpoint" URL found in the
  OpenID Endpoint Configuration of your Keycloak realm
* Token URL: The "token_endpoint" URL found in the
  OpenID Endpoint Configuration of your Keycloak realm
* JWKS URL: The "jwks_uri" URL found in the
  OpenID Endpoint Configuration of your Keycloak realm
