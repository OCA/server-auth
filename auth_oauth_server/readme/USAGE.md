Applications discover the server from
`<issuer>/.well-known/oauth-authorization-server` and each protected API from
`<issuer>/.well-known/oauth-protected-resource<path>`. When a user connects an
application, Odoo asks them to log in if needed, then shows what the
application asks for and where the user will be sent. Once the user allows it,
the application can call the API.

Users see the applications they connected in their preferences (*Account
Security* tab) and can revoke them there. Administrators see every
authorization in *Settings > Users & Companies > OAuth Server*.

To protect a route of your own module, either use the resource's validator in
the route:

```python
@http.route("/api/orders", auth="jwt_oauth_server_api", type="http")
def orders(self):
    if "orders:read" not in request.jwt_payload["scope"].split():
        raise Forbidden()
    ...
```

or check the token yourself, which also gives you the `WWW-Authenticate` header
that lets clients discover the server:

```python
resource = request.env.ref("my_module.my_resource").sudo()
try:
    uid, payload = resource._authenticate_bearer(token, ["orders:read"])
except Unauthorized:
    headers = [("WWW-Authenticate", resource._www_authenticate())]
    ...
```
