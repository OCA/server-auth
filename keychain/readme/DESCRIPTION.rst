This module allows you to store credentials of external systems.

* All the crendentials are stored in one place: easier to manage and to audit.
* Multi-account made possible without effort.
* Store additionnal data for each account.
* Validation rules for additional data.
* Have different account for different environments (prod / test / env / etc).


By default, passwords are encrypted with a key stored in Odoo config.
It's far from an ideal password storage setup, but it's way better
than password in clear text in the database.
It can be easily replaced by another system. See "Security" chapter below.

Accounts may be: market places (Amazon, Cdiscount, ...), carriers (Laposte, UPS, ...)
or any third party system called from Odoo.

This module is aimed for developers.
The logic to choose between accounts will be achieved in dependent modules.

==========
Uses cases
==========

Possible use case for deliveries: you need multiple accounts for the same carrier.
It can be for instance due to carrier restrictions (immutable sender address),
or business rules (each warehouse use a different account).
