.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
    :target: https://www.gnu.org/licenses/agpl
    :alt: License: AGPL-3

==========================
User Role From HTTP Header
==========================

This module extends the functionality of `auth_from_http_remote_user <https://github.com/OCA/server-auth/tree/11.0/auth_from_http_remote_user>`_
as well as `base_user_role <https://github.com/OCA/server-backend/tree/11.0/base_user_role>`_.
It gives the possibility  when the authentication of the remote user has been successful, to
assign roles to the new authenticated user, based on the content of the HTTP header field ``HTTP_REMOTE_ROLE``.


Installation
============

Install this module like any other module.


Configuration
=============

When the module ``auth_from_http_remote_user`` is installed and working. You need to tweak
the HTTP header the same way by adding a field ``HTTP_REMOTE_ROLE``. This field must
contain the codes referencing the pre defined user roles that will be assigned to the user.
It can contain multiple codes separated by a comma.

Those codes can be assigned to preconfigured user roles directly on ther edition page.


Usage
=====

 .. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
    :target: https://runbot.odoo-community.org/runbot/251/11.0
    :alt: Try me on Runbot :


Known issues / Roadmap
======================


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/server-auth/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Thierry Ducrest <thierry.ducrest@camptocamp.com>

Do not contact contributors directly about support or help with technical issues.

Maintainer
----------

 .. image:: https://odoo-community.org/logo.png
    :target: https://odoo-community.org
    :alt: Odoo Community Association

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
