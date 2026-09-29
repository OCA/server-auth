Enable **Link Existing Users by Verified Email** on the provider
(Settings > Users & Companies > OAuth Providers). The option is disabled by
default, per provider.

When an unknown subject logs in, and the provider's claims contain `email`
and `email_verified: true`, the subject is linked to the active user whose
login is that email (case insensitive).

The user's Email field is deliberately not matched: users can edit their own
email, so matching it would let a user attract the first login of someone
else's provider account. The login is the credential, and only administrators
can change it.

No link is made, and the login proceeds as without this module, when:

- `email_verified` is missing or not the JSON boolean `true`;
- several users have the email as login (differing only in case);
- the matching user is already linked to a subject;
- the matching user is a Settings administrator: link those manually, as
  whoever controls their email at the provider would otherwise gain
  administrator access.

Only enable this option for providers that verify email addresses and return
`email` and `email_verified` in the claims Odoo reads. With OpenID Connect
(`auth_oidc`), these are the ID token claims: some providers (e.g. Authelia)
only return them from the userinfo endpoint by default and must be configured
to include them in the ID token.

Disabling signup during the migration makes unmatched users fail loudly
instead of creating duplicates.
