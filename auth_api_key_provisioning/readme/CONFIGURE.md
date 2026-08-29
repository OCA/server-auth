After installing the module:

1. Add your integration / service account to the **API Key Provisioning** group
   (_Settings → Users & Companies → Users_). Do **not** use a system administrator for
   this — the whole point is least privilege.
2. Add each user that integrations may act as to the **API Key Mintable Target** group.

Two system parameters (_Settings → Technical → System Parameters_) tune the lifetime:

- `auth_api_key_provisioning.default_ttl_days` (default `30`) — applied when a mint
  request omits `ttl_days`.
- `auth_api_key_provisioning.max_ttl_days` (default `90`) — requested lifetimes are
  clamped down to this. An absolute ceiling is also enforced in code.
