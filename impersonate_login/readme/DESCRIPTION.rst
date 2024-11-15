This module allows one user (for example, a member of the support team)
to log in as another user. The impersonation session can be exited by
clicking on the button "Back to Original User".

To ensure that any abuse of this feature will not go unnoticed, the
following measures are in place:

-  In the chatter, it is displayed who is the user that is logged as
   another user.
-  Mails and messages are sent from the original user.
-  Impersonated logins are logged and can be consulted through the
   Settings -> Technical menu.
- To prevent users with "Administration: Settings" rights from being impersonated,
   enable the restrict_impersonate_admin_settings field in the settings.
   This will restrict the ability to impersonate users with administrative
   access to the settings.

There is an alternative module to allow logins as another user
(auth_admin_passkey), but it does not support these security mechanisms.
