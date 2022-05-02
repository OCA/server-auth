Configure OAuth providers in Settings > Users and Companies, and make sure
there is one and only one that has both the enabled and automatic login flags
set.

When this is done, users visiting the login page (/web/login), or being
redirected to it because they are not authenticated yet, will be redirected to
the identity provider login page instead of the regular Odoo login page.

Be aware that this module does not actively prevent users from authenticating
with an login and password stored in the Odoo database. In some unusual
circumstances (such as identity provider errors), the regular Odoo login may
still be displayed. Securely disabling Odoo login and password, if needed,
should be the topic of another module.

Also be aware that this has a possibly surprising effect on the logout menu
item. When the user logs out of Odoo, a redirect to the login page happens. The
login page in turn redirects to the identity provider, which, if the user is
already authenticated there, automatically logs the user back in Odoo, in a
fresh session.
