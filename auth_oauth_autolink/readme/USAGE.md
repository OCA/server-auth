Nothing changes for users: they click the provider button on the login page.

The first login of an existing user links the account and logs them in; a
note on the user's partner records it. Later logins go through the stock
`oauth_uid` lookup.

When a condition is not met, the login is refused as stock `auth_oauth` does.
The reason is written to the server log, never shown to the caller.
