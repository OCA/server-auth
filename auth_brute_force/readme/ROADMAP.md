* Depending of server and / or user network configuration, the idenfication
  of the user can be wrong, and mainly in the following cases:

  * If the Odoo server is behind an Apache / NGinx proxy and it is not properly
    configured, all requests will use the same IP address. Blocking such IP
    could render Odoo unusable for all users! **Make sure your logs output the
    correct IP for werkzeug traffic before installing this addon.**

* The IP metadata retrieval should use a better system. `See details here
  <https://github.com/OCA/server-tools/pull/1219/files#r187014504>`_.
