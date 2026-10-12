Stock `auth_oauth` recognises a user only by the `oauth_uid` stored on the
user record. A user created by an administrator has none, so the first OAuth
login falls through to signup and, where signup is disabled, is refused. The
stock workarounds are opening signup or filling in the provider's identifier
on every user by hand.

With this module, the first OAuth login is linked to the existing user whose
login is the e-mail address the provider verified. After that, the stock
`oauth_uid` lookup takes over.

The link is made only when all of these hold:

- the provider has **Auto-link existing users by email** ticked (off by
  default);
- the provider reports the e-mail as verified (`email_verified`, or the
  legacy `verified_email`); an absent claim counts as not verified;
- exactly one active user has that e-mail as login, compared
  case-insensitively;
- that user is not linked to an OAuth account yet, so an existing link is
  never moved;
- that user is not an administrator (`base.group_system`): whoever controls
  that mailbox at the provider would otherwise get administrator access.
  Administrators are linked by hand.

Otherwise the login behaves as without this module: the same refusal, with
the reason written to the server log only.

When a link is made, `oauth_provider_id` and `oauth_uid` are written on the
user and a note is posted on the user's partner.

It works for the providers of `auth_oauth` and for the OpenID Connect flows
of `auth_oidc`.

**The trust anchor is the provider's verified-email claim.** If a provider
lets anyone claim an arbitrary e-mail address, ticking the option lets them
take over the matching Odoo account. Enable it only for providers you control
or trust to verify e-mail ownership, such as a Google Workspace domain.
