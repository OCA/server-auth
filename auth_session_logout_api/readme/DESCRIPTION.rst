This module provides a secure API endpoint to force logout user sessions remotely.

**Features:**

* Token-based authentication via HTTP headers (prevents token exposure in logs)
* Supports both custom header and standard Bearer authentication
* Lookup users by login or email (case insensitive)
* Comprehensive audit logging for all API requests
* Session invalidation via Odoo's session token mechanism

When a force logout is triggered, the module updates a special field that is part of the session token computation.
This invalidates all existing sessions for the target user, forcing them to re-authenticate.
