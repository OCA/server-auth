1. Open `https://<instance>/auth_admin_sso/login`,
  &rArr; this redirects you to your IdP
2. log in with your provider account (e.g. Entra ID)
  &rArr; You get redirected to Odoo and logged as
   - `<username>`, if you have the role
     `<required role>.username.<username>`;
   - else the default login (`admin` unless configured), if you have the
     role `<required role>`;
   - else the login is refused.

## Access from login form

With `AUTH_ADMIN_SSO_REDIRECT_LOGIN` enabled, the login form can start the SSO:

1. Login: the default login (`admin` unless configured).
2. Password: the redirect keyword (`sso` unless configured).
   It is not a secret: it only redirects to the provider login,
   which still checks your account and role.

Any other login or password gets the usual Odoo password check.


## MFA/2FA

The Odoo two-factor authentication of that user is not asked:
the provider is responsible for it.
Each login is logged with the email from the provider.

## Login Failure

When the login fails, the page only shows a reference (a random UUID),
never the cause. Give that reference to an administrator: the server log
has a warning with the same reference and the exact cause.
