To use this module, you need an IDP server, properly set up. Go through the
"Getting started" section for more information.

There are SAML-related settings in :menuselection:`Configuration --> General Settings`.

Configuring Odoo
----------------

#. **Configure your auth provider** going to *Settings > Users & Companies >
   SAML Providers > Create*. Your provider should provide you all that info.
#. Go to *Settings > Users & Companies > Users* and edit each user that will
   authenticate through SAML.
#. Go to the *SAML* tab and fill both fields.
#. Go to *Settings > General settings* and uncheck *Allow SAML users to posess
   an Odoo password* if you want your SAML users to authenticate only
   through SAML.
