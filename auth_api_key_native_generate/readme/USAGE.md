Request a key by POSTing JSON credentials to the endpoint:

```
POST /api/auth/generate_api_key
Content-Type: application/json

{
  "db": "mydb",
  "login": "user@example.com",
  "password": "the-user-password"
}
```

On success (HTTP 200) the response holds the key and its expiration date
(ISO 8601, UTC):

```json
{
  "api_key": "0123456789abcdef...",
  "expiration_date": "2026-10-11T09:30:00+00:00"
}
```

Error responses:

- `400`: missing `db`, `login` or `password`, or a body that is not a JSON object.
- `401`: invalid credentials.
- `403`: the user has two-factor authentication enabled, so a password alone cannot issue a key.
- `404`: unknown database.
- `413`: request body too large.

Use the returned `api_key` as the bearer credential for the native Odoo
`/json/2` and RPC endpoints, in place of the user password:

```
curl -H "Authorization: Bearer 0123456789abcdef..." \
     https://mydb.example.com/json/2/...
```
