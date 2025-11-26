Admin user have the possibility to unblock a banned IP.

Logging
-------

This module generates some WARNING logs, in the following cases:

* When the IP limit is reached: *Authentication failed from remote 'x.x.x.x'.
  The remote has been banned. Login tried: xxxx.*

* When the IP+user combination limit is reached:
  *Authentication failed from remote 'x.x.x.x'.
  The remote and login combination has been banned. Login tried: xxxx.*

Screenshot
----------

**List of Attempts**

.. image:: /auth_brute_force/static/description/screenshot_attempts_list.png
