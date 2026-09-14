The impersonating user must belong to group "Impersonate Users".

A log is closed as soon as the impersonating user goes back to their own user
or logs out. When a session is simply abandoned, the log is closed by the daily
"Vacuum" scheduled action, once the session can no longer be used. The last
known activity is then recorded as the end date. That delay follows the
standard Odoo system parameter `sessions.max_inactivity_seconds` (7 days by
default); lower it if you want dangling logs to be closed sooner.
