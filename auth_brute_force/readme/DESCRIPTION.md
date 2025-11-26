This module registers each request done by users trying to authenticate into
Odoo. If the authentication fails, a counter is increased for the given remote
IP. After a defined number of attempts, Odoo will ban the remote IP and
ignore new requests.

This module applies security through obscurity
(https://en.wikipedia.org/wiki/Security_through_obscurity).
When a user is banned, the request is now considered as an attack. So, the UI
will **not** indicate to the user that his IP is banned and the regular message
'Wrong login/password' is displayed.

This module realizes a call to a web API (http://ip-api.com) to try to have
extra information about remote IP.
