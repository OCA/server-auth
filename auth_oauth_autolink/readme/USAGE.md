Nothing changes for the user: they click the provider button on the login page
as usual.

The first time an existing Odoo user logs in through a provider with the flag
enabled, and the provider reports their e-mail address as verified, their
account is linked to that OAuth account and they are logged in. A note is
posted on the user's partner chatter recording the link, and the server log
gets an INFO line.

Every subsequent login goes through the stock `oauth_uid` lookup, so the
module adds no extra queries after the first one.

When any of the conditions is not met the login is refused exactly like stock
`auth_oauth` does. The reason is written to the server log, never disclosed to
the caller.
