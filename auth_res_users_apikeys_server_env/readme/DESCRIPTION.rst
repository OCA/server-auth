Configure api api keys via server env.

This can be very useful to avoid mixing your keys between your various
environments when restoring databases.

You have choice to configure with [server_environment](https://github.com/OCA/server-env/tree/14.0/server_environment)
configuration such as::

```
[res_users_apikeys.my_user]
key="*****secret*****"
```

Or using [server_environment_data_encryption](https://github.com/OCA/server-env/tree/14.0/server_environment_data_encryption)
password will be saved in the database encrypted with secrets provided in your configuration.
In such case admin view is the best fit to edit those keys Configuration > Technical >
