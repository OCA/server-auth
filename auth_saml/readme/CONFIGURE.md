To use this module, you need an IDP server, properly set up.

1.  Configure the module according to your IdP’s instructions (Settings
    \> Users & Companies \> SAML Providers).
2.  Pre-create your users and set the SAML information against the user.

By default, the module let users have both a password and SAML ids. To
increase security, disable passwords by using the option in Settings.
Note that the admin account can still have a password, even if the
option is activated. Setting the option immediately remove all password
from users with a configured SAML ids.

If all the users have a SAML id in a single provider, you can set
automatic redirection in the provider settings. The autoredirection will
only be done on the active provider with the highest priority. It is
still possible to access the login without redirection by using the
query parameter `disable_autoredirect`, as in
`https://example.com/web/login?disable_autoredirect=` The login is also
displayed if there is an error with SAML login, in order to display any
error message.

If you are using Office365 as identity provider, set up the federation metadata document
rather than the document itself. This will allow the module to refresh the document when
needed. 

