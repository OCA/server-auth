This module uses the standard **Administration / Settings** group (``base.group_system``)
for access control. Only users with this group can:

* View and generate the force logout API token
* View all audit logs

To generate the API token:

#. Go to **Settings** → **General Settings**
#. Find the **Force Session Logout** section
#. Click **Generate Token** to create a new secure token
#. Copy the token and store it securely for use in API calls

**Security considerations:**

* The token is transmitted via HTTP headers (not URL) to prevent exposure in logs
* Store the token securely and rotate it periodically
* Consider implementing rate limiting at the reverse proxy level
* All API calls are logged for auditing purposes

To view audit logs:

#. Go to **Settings** → **Technical** → **Security** → **Force Logout Audit**
