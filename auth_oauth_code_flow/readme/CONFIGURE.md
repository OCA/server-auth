## Automatic System Parameters

Upon installation, this module automatically configures the following system parameter:

  - auth_oauth.authorization_header: Set to 1.

Purpose: This forces Odoo to send the access_token in the HTTP Authorization Header (Bearer <token>) rather than as a query parameter in the URL.
GitHub and most modern providers have deprecated URL-based tokens for security reasons.
