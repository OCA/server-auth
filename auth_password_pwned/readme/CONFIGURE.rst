ir.config_parameter options
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following config parameters change the behaviour of this addon.

``auth_password_pwned.range_url`` *string* (Default: https://api.pwnedpasswords.com/range/)

  Change the url the plugins checks hashes against. Needs to behave like described in
  https://haveibeenpwned.com/API/v3#SearchingPwnedPasswordsByRange . This is intended to be used for a company mirror
  of the API.
