.. |badge1| image:: https://img.shields.io/badge/maturity-stable-green.png
    :target: https://odoo-community.org/page/development-status
    :alt: Stable

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fserver--auth-lightgray.png?logo=github
    :target: https://github.com/OCA/server-auth/tree/11.0/auth_saml
    :alt: OCA/server-auth

.. |badge5| image:: https://img.shields.io/badge/runbot-Try%20me-875A7B.png
    :target: https://runbot.odoo-community.org/runbot/251/11.0
    :alt: Try me on Runbot

|badge1| |badge2| |badge3| |badge5|

====================
SAML2 authentication
====================

Let users log into Odoo via an SAML2 provider.

This module allows to deport the management of users and passwords in an
external authentication system to provide SSO functionality (Single Sign On)
between Odoo and other applications of your ecosystem.

.. WARNING::

    This module requires auth_crypt. This is because you still have the
    option if not recommended to allow users to have a password stored in odoo
    at the same time as having a SAML provider and id.


Benefits
========

* Reducing the time spent typing different passwords for different accounts.

* Reducing the time spent in IT support for password oversights.

* Centralizing authentication systems.

* Securing all input levels / exit / access to multiple systems without
  prompting users.

* The centralization of access control information for compliance testing to
  different standards.


Installation
============

Install as you would install any Odoo addon.

Dependencies
------------

This addon requires `lasso`_ ≥ 2.6.0.

.. _lasso: http://lasso.entrouvert.org


Configuration
=============

There are SAML-related settings in Configuration > General settings.


Usage
=====

To use this module, you need an IDP server, properly set up. Go through the
"Getting started" section for more information.


Known issues / Roadmap
======================

* Checks to ensure no Odoo user with SAML also has an Odoo password.
* Setting to disable that rule.

2.0
---

* SAML tokens are not stored in res_users anymore to avoid locks on that table.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/server-auth/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback `here <https://github.com/OCA/
server-auth/issues/new?body=module:%20
auth_saml%0Aversion:%20
11.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

In order of appearance:

- Florent Aide <florent.aide@xcg-consulting.fr>
- Vincent Hatakeyama <vincent.hatakeyama@xcg-consulting.fr>
- Alexandre Brun <alexandre.brun@xcg-consulting.fr>
- Jeremy Co Kim Len <jeremy.cokimlen@vinci-concessions.com>
- Houzéfa Abbasbhay <houzefa.abba@xcg-consulting.fr>
- Jeffery Chen Fan <jeffery9@gmail.com>
- Bhavesh Odedra <bodedra@opensourceintegrators.com>


Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
