This module forces logout of all active user sessions on a schedule (defaults
to every Sunday at 23:00), regardless of user activity. It's not an inactivity
timeout: even users actively working are logged out at scheduled time. At the
scheduled time every targeted browser session becomes invalid. On next request
the user is redirected to the login page.

Installing or upgrading the module logs nobody out: the timestamp is empty for
existing users, and leaves the token untouched while it is empty, so current
sessions keep working until the scheduled job runs. Users can be excluded from
the logout by adding them to the security group *Exempt from Scheduled Session
Logout*.
