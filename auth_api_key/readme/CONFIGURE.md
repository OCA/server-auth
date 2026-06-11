The api key menu is available into Settings \> Technical in debug mode.
By default, when you create an API key, the key is saved into the
database.

When you create an API key, a random key is generated automatically. You
can replace it manually, or use the Generate Random Token button if an
existing record has no key. The key field is masked by default, and the
password widget provides a button to reveal the value when needed.

When a database is neutralized, stored API key values are cleared.

If you want to manage them via serve environment settings use
auth_api_key_server_env.
