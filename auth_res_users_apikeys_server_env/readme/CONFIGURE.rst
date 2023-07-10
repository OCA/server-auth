
* got to the user preference form
* add new keys for each env on production databases
* set scope of each key regarding target environment with template: `rpc_<env>`
  where `<env>` is the `running_env` used by `server_environment` module.

only api key matching this env would works.

.. note::

    If you keep scope as empty string you would get default behavior and match any env
.. warning::

    Unfortunately as key are already encrypted and key field not expose to the ORM
    on base module we can't configure key in config files as it would be with
    server_environment and server_environment_data_encryption
