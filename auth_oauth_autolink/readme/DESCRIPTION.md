This module lets users that **already exist in Odoo** log in through an
OAuth provider, without writing the provider's opaque identifier onto every
user record by hand.

## The problem

Stock `auth_oauth` recognises a user only by the `oauth_uid` stored on the
user record (`res.users.oauth_uid` + `oauth_provider_id`). A user created by
an administrator has neither, so the very first OAuth login misses, falls
through to the signup path and -- on a B2B database, where signup is disabled
-- is refused with *"You do not have access to this database..."*. The only
stock workarounds are enabling public signup, which nobody wants on a B2B
database, or filling `oauth_uid` in manually for every user.

## What this module does

On the first OAuth login, when the `oauth_uid` lookup misses, the login is
linked to the existing user whose login is the e-mail address the provider
verified. From then on the stock path takes over and nothing else changes.

The link is performed **only** when *all* of the following hold:

1. The provider has **Auto-link existing users by email** ticked
   (`auth.oauth.provider.autolink_by_email`, off by default).
2. The provider reports the e-mail as **verified** -- the `email_verified`
   (OpenID Connect) or `verified_email` (legacy Google tokeninfo) claim. An
   absent claim counts as *not verified*.
3. Exactly **one active** user matches `login == email`, compared with Odoo's
   own `email_normalize`, so the match is case-insensitive unlike Odoo's
   case-sensitive login.
4. That user has **no `oauth_uid`** yet.

Anything else behaves exactly like stock `auth_oauth`: the same
`AccessDenied`, with no hint about which condition refused.

When a link is made, the module writes `oauth_provider_id` and `oauth_uid`,
logs at INFO level and posts a note on the user's partner chatter
(`res.users` is not a `mail.thread`).

The link is performed in `_auth_oauth_validate`, right after the provider
vouched for the identity and *before* the sign-in chain starts. By the time
`_auth_oauth_signin` runs, the user is an ordinary already-linked user, so
the stock implementation stores the access token as it always does and other
modules overriding the sign-in -- `auth_oauth_multi_token`, for one -- need no
cooperation from this one. Linking before sign-in is also what keeps a
signup-enabled (B2C) database safe: the stock flow would otherwise try to
*create* a user with the very login about to be linked, which fails on the
`login` unique index and poisons the transaction.

## Security model

**The trust anchor is the provider's verified-email claim.** If a provider
lets anyone claim an arbitrary e-mail address, ticking this flag lets that
someone take over the matching Odoo account. Only enable it for providers you
control, or trust to verify e-mail ownership -- a Google Workspace domain is
the intended case.

The consequences of the guards above, spelled out:

- An **already-linked** user is never re-pointed at another OAuth account, so
  the flag can never be used to hijack an account that already logs in.
- An **archived** user is never linked (`search` excludes archived records),
  so deactivating a user still ends their access.
- An **ambiguous** e-mail (two users whose logins differ only in case) is
  refused rather than resolved arbitrarily.
- **Portal and public users are eligible**, deliberately: a portal customer
  whose login is their verified e-mail may use the same provider. If that is
  not wanted, do not enable the flag; there is no separate switch.
- The module never widens what OAuth can do: it only replaces a refusal with a
  link to an account that *already* exists.
