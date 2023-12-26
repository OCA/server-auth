Configure api keys via server env.

This can be very useful to avoid mixing your keys between your various
environments when restoring databases. All you have to do is to add a
new section to your configuration file according to the following
convention:

``` ini
[api_key_<record.tech_name>]
key=my_api_key
```
