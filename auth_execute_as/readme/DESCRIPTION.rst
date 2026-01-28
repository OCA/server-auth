This module provides a secure API endpoint that allows external systems to
execute Odoo methods as a specific user.

The key feature is **User Impersonation** - executing actions under a specific
user's identity so that all Odoo access controls (ACLs & Record Rules) are
automatically applied.

**Security Architecture**

The module manages access through 3 layers:

* **API Client**: Identifies the connecting application/service with a secret token
* **API Whitelist**: Groups permissions by purpose (e.g., "Sales Agent Group")
* **API Whitelist Line**: Defines allowed Model + Method combinations and field restrictions

**Features**

* Token-based authentication via ``X-API-Key`` header
* IP address whitelist (supports CIDR notation)
* Token expiration dates
* User whitelist per client
* Field-level access control
* Request/response logging with execution time metrics
* LLM-friendly response formatting (simplified Many2one fields, ISO dates)

**API Endpoint**

``POST /execute_as``

Request body::

    {
        "login": "user@example.com",
        "model": "sale.order",
        "method": "search_read",
        "args": [[["state", "=", "sale"]]],
        "kwargs": {
            "fields": ["name", "amount_total"],
            "limit": 10
        }
    }

**HTTP Status Codes**

* 200 - Success
* 401 - Invalid or missing API key, expired token
* 403 - Method not whitelisted, IP not allowed, user not allowed
* 404 - User or record not found
* 422 - Validation error (Odoo UserError/ValidationError)
* 500 - Internal server error
