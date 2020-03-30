The API key menu is available into Settings > Technical in debug mode.
By default, when you create an API key, the key is saved into the database.

Using Server Environment, it is also possible to provide the value of this key
via the configuration file.
This can be very useful to avoid mixing your keys between your various
environments when restoring databases.i

All you have to do is to add a new
section to your configuration file according to the following convention:

.. code-block:: ini

    [api_key_<Record Name>]
    key=my_api_key
