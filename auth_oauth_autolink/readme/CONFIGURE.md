1. Activate the developer mode.
2. Go to **Settings > Users & Companies > OAuth Providers** and open the
   provider.
3. Tick **Auto-link existing users by email**.

The option is per provider and off by default. Enable it only for a provider
you trust to verify e-mail ownership.

Administrators are never linked automatically. To link one by hand, open the
user and, in the **Oauth** tab, set **OAuth Provider** and **OAuth User ID**
(the identifier the provider reports for that account, `sub` in OpenID
Connect).
