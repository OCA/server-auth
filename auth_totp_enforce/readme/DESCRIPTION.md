This module forces internal users to configure two-factor authentication
(a TOTP authenticator app) before they log in.

Enforcement works like the password expiry flow of `password_security`: nobody
is logged out when the module is installed, but on their next login users are
held in a mandatory step and cannot reach the backend until they have enabled
an authenticator app.

Members of the **Exempt from 2FA enforcement** group are never forced. Portal
and public users are out of scope at the moment.
