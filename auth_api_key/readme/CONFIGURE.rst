The api key menu is available into Settings > Technical in debug mode.
By default, when you create an API key, the key is saved into the database.
It is also possible to provide the value of this key via the configuration
file. This can be very useful to avoid mixing your keys between your various
environments when restoring databases. All you have to do is to add a new
section to your configuration file according to the following convention:

.. code-block:: ini

    [api_key_<Record Name>]
    key=my_api_key
