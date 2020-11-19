=================================
Authentication via OpenID Connect
=================================

This module allows users to login through an OpenID Connect provider.

This includes:

- Keycloak with ClientID and secret + Implicit Flow
- Microsoft Azure


Usage
=====

Setup for Microsoft Azure
~~~~~~~~~~~~~~~~~~~~~~~~~

# configure a new web application in Azure with OpenID and implicit flow (see
  the `provider documentation
  <https://docs.microsoft.com/en-us/powerapps/maker/portals/configure/configure-openid-provider)>`_)
# in this application the redirect url must be be "<url of your
  server>/auth_oauth/signin" and of course this URL should be reachable from
  Azure
# create a new authentication provider in Odoo with the following
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

write me...


Credits
=======

Authors
~~~~~~~

* ICTSTUDIO, André Schenkels <https://www.ictstudio.eu>

Contributors
~~~~~~~~~~~~

* Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
