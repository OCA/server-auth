In *Settings > General Settings > OAuth Authorization Server*:

- **OAuth Issuer URL**: the public HTTPS address of Odoo, as applications reach
  it. It is set from `web.base.url` at installation; check it, especially
  behind a reverse proxy (where `proxy_mode` must be enabled too). Changing it
  invalidates the access tokens issued so far; applications get new ones with
  their refresh tokens.
- **Accept Client Metadata Documents**: let applications identify themselves
  with the URL of the details they publish, without being registered first.
  Odoo then fetches that URL, from public addresses only. List the domains to
  accept: when the list is empty, any domain is.
- **Allow Dynamic Client Registration**: let applications register themselves.
  Enable it only for applications that publish no metadata document and that
  you do not want to register by hand.

Both are off at installation. Whoever may register an application chooses its
name, and could pass it off as a well-known one to have users approve it: the
consent page shows the domain that published a metadata document, and warns
that the name of a self-registered application is not verified.

Then, in *Settings > Users & Companies > OAuth Server > Protected Resources*,
declare each API that accepts the tokens: its path on this server, the scopes
applications may ask for, the groups whose users may give access (all internal
users when empty), and the lifetime of tokens.

Applications to be registered by hand go in *OAuth Applications*. Give them
the Client ID and, for confidential ones, the secret shown by *Generate
Secret*.

With several databases on one server, set `dbfilter` so that each host name
selects one database: the endpoints of this module are called without a
session, so they cannot work otherwise.
