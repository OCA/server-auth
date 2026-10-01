- The e-mail is matched against `res.users.login` only. Matching against the
  partner's `email` field is deliberately not done: `login` is the credential,
  `email` is not unique and is not an authentication attribute.
- There is no separate switch to exclude portal or public users from the
  matching. If those must be excluded, do not enable the flag on that
  provider.
