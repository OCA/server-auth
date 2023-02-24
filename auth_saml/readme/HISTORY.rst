15.0.1.4.0
~~~~~~~~~~

Handle redirect after authentification.

15.0.1.3.0
~~~~~~~~~~

Improve login page.

15.0.1.1.0
~~~~~~~~~~

Fix the module by adding a transaction to commit the token.

Fix the disallow password for users with SAML ids.
Added tests to ensure the feature works correctly.
Admin user is also an exception from not having a password. In Odoo 15.0, this is the standard user to connect for administrative task, not the super user.

Improve provider form and list views.

Add auto redirect on providers. Use disable_autoredirect as a parameter query to disable automatic redirection (for example ``https://example.com/web/login?disable_autoredirect=``)

Add certificate file name fields to improve the UI.

Add required on several fields of the SAML provider; without them the server will crash and there is not enough information to make SAML work.

Split signing to have finer control and be compatible with more IDP.

Integrate token into res.users.saml, removing auth_saml.token. No need for a separate table, and no more need to create lines in the table.

Avoid server errors when user try metadata page without necessary parameters.

Replace method call from ``odoo.http.redirect_with_hash`` to ``request.redirect`` as the former does not exists in Odoo 15.0 anymore.

Improved the module documentation.

15.0.1.0.0
~~~~~~~~~~
