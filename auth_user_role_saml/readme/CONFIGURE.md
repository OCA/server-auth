To configure SAML role synchronization:

1. Ensure your SAML Identity Provider is configured to send user attributes (e.g., `groups`, `roles`, or `department`) in its SAML assertions.
2. Configure your attribute mappings in **Settings > Users & Companies > Identity Role Mappings** (provided by the base `auth_user_role` module).
3. Navigate to **Settings > Users & Companies > SAML Providers** and open your provider.
4. Under the provider settings, you will find a **Strict Role Synchronization** checkbox:
   * **Unchecked (Default):** Additive mode. Mapped roles are granted, but manually assigned roles in Odoo are left completely untouched.
   * **Checked:** Strict mode. Odoo becomes a strict mirror of the IdP. Any roles the user possesses in Odoo that are *not* explicitly granted by the current SAML payload will be automatically removed upon login.