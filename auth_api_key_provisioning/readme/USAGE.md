From a provisioning/service account (a member of _API Key Provisioning_), call the
method over RPC on the target user. The target must be an internal user that is a member
of the _API Key Mintable Target_ group.

```python
import xmlrpc.client

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "prov-svc", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Mint a 7-day rpc key for user id 42:
api_key = models.execute_kw(
    db, uid, password,
    "res.users", "mint_apikey", [[42]],
    {"name": "my-integration", "ttl_days": 7},
)

# Later, revoke everything this module minted for that user:
models.execute_kw(db, uid, password, "res.users", "revoke_provisioned_apikeys", [[42]])
```

The integration then authenticates as user 42 using `api_key` as the password on
RPC/`/xmlrpc/2/object` calls; Odoo applies that user's own ACLs and record rules.

## Security model

- **Caller gating** — only members of _API Key Provisioning_ may mint or revoke; this is
  a dedicated least-privilege group, **not** `base.group_system`.
- **Target allowlist** — keys are minted only for users explicitly placed in _API Key
  Mintable Target_. An allowlist is used rather than a blocklist because custom modules
  add their own high-privilege groups that no fixed blocklist could enumerate.
- **Elevated targets refused** — minting is always refused for the superuser and for any
  member of `base.group_system` / `base.group_erp_manager`, even if mis-added to the
  allowlist. Portal/public (share) and archived users are refused too.
- **Privilege-drift protection** — API keys carry no permission snapshot; they
  authenticate with the user's _current_ groups. If a target with minted keys is later
  promoted into an elevated group (from the user side or the group side) or archived,
  its provisioned keys are revoked immediately; a daily cron is a backstop for changes
  that bypass the ORM hooks.
- **Bounded lifetime** — keys are always `rpc`-scoped and expiring. The TTL defaults to
  30 days and is clamped to a configurable maximum (90 days), with an absolute code
  ceiling.
- **Auditable** — every mint is logged with who/for-whom/when and a revocation
  timestamp.

## Residual risks (by design)

- Like all Odoo API keys, a minted key is **not** invalidated by a target password
  reset. Use `revoke_provisioned_apikeys` (or archive the user) on a suspected
  compromise.
- A compromised provisioning account can mint keys for any _mintable_ (non-elevated)
  user. Keep that group's membership minimal and monitor the provisioning log.
