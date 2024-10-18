If all the users have a oauth id in a single provider, you can set automatic redirection
in the provider settings. The autoredirection will only be done on the active provider
with the highest priority. It is still possible to access the login without redirection
by using the query parameter ``disable_autoredirect``, as in
``https://example.com/web/login?disable_autoredirect=`` The login is also displayed if
there is an error with login, in order to display any error message.
