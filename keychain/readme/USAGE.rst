Usage (for module dev)
======================


* Add this keychain as a dependency in __manifest__.py
* Subclass `keychain.account` and add your module in namespaces:  `(see after for the name of namespace )`

.. code:: python

    class LaposteAccount(models.Model):
        _inherit = 'keychain.account'

        namespace = fields.Selection(
            selection_add=[('roulier_laposte', 'Laposte')])

* Add the default data (as dict):

.. code:: python

    class LaposteAccount(models.Model):
        # ...
        def _roulier_laposte_init_data(self):
            return {
                "agencyCode": "",
                "recommandationLevel": "R1"
            }

* Implement validation of user entered data:

.. code:: python

    class LaposteAccount(models.Model):
        # ...
        def _roulier_laposte_validate_data(self, data):
            return len(data.get("agencyCode") > 3)

* In your code, fetch the account:

.. code:: python

    import random

    def _get_auth(self):
        keychain = self.env['keychain.account']
        if self.env.user.has_group('stock.group_stock_user'):
            retrieve = keychain.suspend_security().retrieve
        else:
            retrieve = keychain.retrieve

        accounts = retrieve(
            [['namespace', '=', 'roulier_laposte']])
        account = random.choice(accounts)
        return {
            'login': account.login,
            'password': account.get_password()
        }


In this example, an account is randomly picked. Usually this is set according
to rules specific for each client.

You have to restrict user access of your methods with suspend_security().

Warning: _init_data and _validate_data should be prefixed with your namespace!
Choose python naming function compatible name.

Switching from prod to dev
==========================

You may adopt one of the following strategies:

* store your dev accounts in production db using the dev key
* import your dev accounts with Odoo builtin methods like a data.xml (in a dedicated module).
* import your dev accounts with your own migration/cleanup script
* etc.

Note: only the password field is unreadable without the proper key, login and data fields
are available on all environments.

You may also use a same `technical_name` and different `environment` for choosing at runtime
between accounts.

Usage (for user)
================

Go to *settings / keychain*, create a record with the following

* Namespace: type of account (ie: Laposte)
* Name: human readable label "Warehouse 1"
* Technical Name: name used by a consumer module (like "warehouse_1")
* Login: login of the account
* Password_clear: For entering the password in clear text (not stored unencrypted)
* Password: password encrypted, unreadable without the key (in config)
* Data: a JSON string for additionnal values (additionnal config for the account, like: `{"agencyCode": "Lyon", "insuranceLevel": "R1"})`
* Environment: usually prod or dev or blank (for all)



.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/server-tools/9.0
