API Endpoint
~~~~~~~~~~~~

To force logout a user, make a POST request to::

    POST /web/session/force_logout?user=LOGIN_OR_EMAIL

**Authentication:**

The API uses token-based authentication via HTTP headers. You can use either:

* ``X-Force-Logout-Token: TOKEN`` - Custom header
* ``Authorization: Bearer TOKEN`` - Standard Bearer authentication

**Parameters:**

* ``user`` (required): User login or email address to force logout (query parameter)

**Example using cURL:**

.. code-block:: bash

    # Using X-Force-Logout-Token header
    curl -X POST "https://your-odoo.com/web/session/force_logout?user=john.doe" \
         -H "X-Force-Logout-Token: your-secure-token"

    # Using Authorization Bearer header
    curl -X POST "https://your-odoo.com/web/session/force_logout?user=john@example.com" \
         -H "Authorization: Bearer your-secure-token"

**Response Codes:**

* ``200 OK`` - User successfully logged out

  .. code-block:: json

      {"success": true, "message": "User \"john.doe\" has been logged out successfully"}

* ``401 Unauthorized`` - Invalid or missing token

  .. code-block:: json

      {"error": "Unauthorized", "message": "Invalid or missing authentication token"}

* ``404 Not Found`` - User not found

  .. code-block:: json

      {"error": "User not found", "message": "User with login or email \"unknown\" not found"}

* ``500 Internal Server Error`` - Server error

Viewing Audit Logs
~~~~~~~~~~~~~~~~~~

#. Go to **Settings** → **Technical** → **Security** → **Force Logout Audit**
#. View the list of all force logout operations
#. Use filters to search by status, date, or target user
