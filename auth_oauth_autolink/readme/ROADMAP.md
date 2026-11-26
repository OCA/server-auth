- The e-mail is matched against `res.users.login` only, never against the
  partner's `email`, which is not unique and is not a credential.
- Portal users are eligible. There is no switch to exclude them other than
  leaving the option off for that provider.
- With both `auth_oidc` and `auth_oauth_multi_token` installed, the first
  login through an OpenID Connect flow (`id_token`, `id_token_code`) is not
  linked: it is refused, as without this module. `auth_oauth_multi_token`
  looks the user up before the rest of the sign-in runs and refuses the login
  when that lookup was empty. This is fixed in 19.0
  ([#1026](https://github.com/OCA/server-auth/pull/1026)) and not in 18.0
  yet; until then, link those users by hand. Plain OAuth2 providers are not
  affected, with or without `auth_oauth_multi_token`.
