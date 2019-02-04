Changelog
=========

__ 11.0.1.1.0::

11.0.1.1.0
----------

- Add auto redirect on providers. Use disable_autoredirect as a parameter query
  to disable autoredirect (for example https://example.com/web/login?disable_autoredirect)
- changes in the form and list of providers
- providers are sorted by sequence then name rather than by name.

11.0.1.0.2
----------

- Fix setting saml_uid on user with password
- Block setting password when not allowed

11.0.1.0.1
----------

Viewing SAML providers does not need to be in debug mode anymore.
