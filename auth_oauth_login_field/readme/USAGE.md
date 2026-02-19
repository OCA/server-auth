If a `login` field is present in the token, it will be used as `login` field on
user signup. When using the ``auth_oidc`` module, the Token Map can be populated
like this, for instance: ``preferred_username:login``.
