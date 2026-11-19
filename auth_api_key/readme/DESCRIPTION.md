Authenticate http requests from an API key.

API keys are codes passed in (in the http header API-KEY) by programs
calling an API in order to identify -in this case- the calling program's
user.

Take care while using this kind of mechanism since information into http
headers are visible in clear. Thus, use it only to authenticate requests
from known sources.

For unknown sources, it is a good practice to filter out this header at
proxy level.

Odoo allows users to authenticate `XMLRPC/JSONRPC` calls using their API key instead of a password by native API keys (`res.users.apikey`). However, `auth_api_key` has some special features of its own such as:
- API keys remain usable even when the user is inactive, if enabled via settings (e.g., for system users in a shopinvader case).
- Supports dual authentication via Basic Auth and API_KEY in separate HTTP headers.
- Admins can manage API keys for all users

Given these advantages, particularly in use case like system user authentication, we have decided to keep the `auth_api_key` module