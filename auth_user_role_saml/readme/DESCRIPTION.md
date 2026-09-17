This is a glue module that bridges `auth_saml` and `auth_user_role`. 

It intercepts the standard SAML sign-in process, extracts the identity payload (attributes) from the SAML response, and passes it to the generic role evaluation engine.
This allows administrators to automatically provision Odoo roles based on groups or attributes defined in Azure AD, Keycloak, Okta, or any other SAML 2.0 Identity Provider.