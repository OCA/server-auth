Restrict the ability to authenticate via regular password authentication, to a
whitelist of IP addresses.

This module allows you to conditionally disable password authentication, which
can be useful in combination with other authentication modules as an
alternative.

Also, the conventional email & password fields on the login screen are hidden by
default. In order to use them, you can show them again by adding `?debug=1` in
the url.
