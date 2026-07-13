Go to **Settings > General Settings > Integrations > API Key Generation
Endpoint** to set the validity window, in days, applied to newly generated API
keys. The value is stored in the `auth_api_key_native_generate.duration` system
parameter (default: `90`).

Notes on the key lifecycle:

- The validity window is fixed. There is no rolling or automatic renewal.
- Changing the duration only affects keys generated afterwards. Existing keys
  keep their own expiration date.
- Generating a key does not revoke the user's other keys, so the same user can
  hold valid keys on several devices (with no maximum number of devices)

## Reverse proxy hardening (recommended)

This endpoint exposes a credential-exchange surface. Add these protections at
the reverse proxy layer:

- HTTP Basic Authentication in front of `/json/2` and
  `/api/auth/generate_api_key`.
- Rate limiting on `/api/auth/generate_api_key` (for example 6 requests per
  minute per IP) to slow down brute-force attempts in multi-worker deployments.

The new endpoint relies on Odoo's native login cooldown (`_assert_can_auth`), which
throttles per client IP using `request.httprequest.remote_addr`. When Odoo runs
behind a reverse proxy, enable proxy mode (`--proxy-mode` / `proxy_mode = True`)
and have the proxy forward `X-Forwarded-For`, so the cooldown sees the real
client IP. Otherwise every request shares one IP and the per-IP protection is
useless.
