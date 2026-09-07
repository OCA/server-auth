This module lets a trusted provisioning/service account **mint a short-lived,
`rpc`-scoped API key on behalf of another internal user**, over RPC.

It exists for _delegated per-user identity_: when an external integration (an MCP
server, an AI agent, or any backend service) needs to act **as an end user** rather than
as a single shared service account. A key minted for the target user carries only that
user's own permissions, so subsequent calls apply Odoo's native record rules and record
the real user as `create_uid`/`write_uid` — instead of attributing everything to one
shared account.

Stock Odoo has no supported way to mint an API key _for another user_ over RPC:
`res.users.apikeys.generate` is not exposed as an RPC method and `_generate` is private.
This module adds two narrowly-scoped, group-gated methods on `res.users` to close that
gap safely.

## What it adds

- `res.users.mint_apikey(name=None, ttl_days=None) -> str` — called on the target user
  recordset; returns a freshly generated `rpc`-scoped key once.
- `res.users.revoke_provisioned_apikeys() -> int` — revokes all keys this module minted
  for that user.
- An auditable log (`auth.api.key.provisioning.log`) of every mint, visible under
  _Settings → Users → Provisioned API Keys_.

MCP / AI-agent usage is the motivating example, but the module itself is generic.
