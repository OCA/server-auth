To use this module, you need to configure a master encryption key in your
``odoo.conf`` file:

1. Generate a URL-safe base64-encoded 32-byte key. You have two options:
   
   **Option A (Recommended - UI Wizard):**
   - Log in as an Administrator (with "Settings" access).
   - Go to Settings > Technical > Security > Generate Encryption Key (Fernet).
   - Copy the generated key.

   **Option B (Terminal):**
   .. code-block:: python

      from cryptography.fernet import Fernet
      print(Fernet.generate_key().decode())

2. Add the copied key to your configuration file under the ``[options]`` section:

   .. code-block:: ini

      [options]
      encryption_key = <YOUR_GENERATED_KEY>

3. Restart your Odoo server.

If no key is configured, or the key is invalid, the module will log a warning
and fallback to storing data in plaintext to prevent data loss.

**WARNING:** The encryption key is NOT stored in the database. If you lose
the key, all previously encrypted fields will become permanently unreadable.
Keep your ``odoo.conf`` safe.
