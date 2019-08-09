* External calls to the Odoo XML-RPC API are blocked for users who enable MFA
  since there is currently no way to perform MFA authentication as part of this
  process. However, due to the way that Odoo handles authentication caching,
  multi-threaded or multi-process servers will need to be restarted before the
  block can take effect for users who have just enabled MFA.
* Make the lifetime of the trusted device cookie configurable rather than fixed
  at 30 days
* Add device fingerprinting to the trusted device cookie
* Add company-level settings for forcing all users to enable MFA and disabling 
  the trusted device option
* Monkey patch 1 is not needed anymore in Werkzeug==0.13 or upper
* Monkey patch 2 will work until werkzeug.contrib gets removed.
