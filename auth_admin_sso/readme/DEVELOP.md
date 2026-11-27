Another add-on adds a provider by inheriting the `AdminSSO`
controller and overriding its `_auth_admin_sso_*` methods (also as a server wide
module, since there is no model):

```python
from odoo.addons.auth_admin_sso.controllers.main import AdminSSO


class MyAdminSSO(AdminSSO):
    def _auth_admin_sso_authorization_url(self, settings, redirect_uri, state, nonce,
                               challenge):
        if settings["provider"] != "my_provider":
            return super()._auth_admin_sso_authorization_url(
                settings, redirect_uri, state, nonce, challenge)
        return "https://my-provider.example.com/authorize?..."

    # Same for _auth_admin_sso_fetch_claims, _auth_admin_sso_check_nonce, _auth_admin_sso_get_roles and
    # _auth_admin_sso_get_identity.
```

Then set `AUTH_ADMIN_SSO_PROVIDER=my_provider`. Every step of the flow is
an overridable `_auth_admin_sso_*` method of `AdminSSO` (e.g. `_auth_admin_sso_select_login`,
`_auth_admin_sso_login_as`). The settings methods (`_auth_admin_sso_get_settings`, ...) come
from `AdminSSOSettingsMixin`, shared with the `/web/login` override
`AdminSSOHome`: override them in a subclass of both controllers.
