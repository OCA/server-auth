Authenticate http requests from an API key.

API keys are codes passed in (in the http header API-KEY)
by programs calling an API in order to identify -in this case- the calling program's user.

Take care while using this kind of mechanism since information into http headers are visible in clear.
Thus, use it only to authenticate requests from known sources.

For unknown sources, it is a good practice to filter out this header at proxy level.
