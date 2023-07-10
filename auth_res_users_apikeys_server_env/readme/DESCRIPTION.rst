Configure API keys (`res.users.apikeys`) per environment.

This can be very useful when other applications communicate with odoo
over jsonrpc to avoid mixing your keys between various
environments ie: when restoring Odoo production databases to staging/tests/dev environments.

This module let change the scope of your API keys in user form view. This module expect scope
set to `rpc_<env>` where `<env>` is the `running_env` used by `server_environment` module.
