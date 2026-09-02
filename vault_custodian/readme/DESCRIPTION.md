This module adds mandatory Vault Custodians to the vault.

Vault Custodians can be configured in the general settings. These users
are automatically added to every newly created vault and can not be
removed from it. They keep access to the end-to-end encrypted vaults,
for example to recover the data in case an employee leaves the company.
Custodians receive read and share permissions by default; the owner can
additionally grant them write and delete permissions.

Be aware of the security implications by configuring custodians which
results in their access to all end-to-end encrypted vaults. Alternatively,
the business requirement may be solved by appropriate organisational
policies.

The custodian protection only applies while a user is configured as a
custodian. Removing a user from the setting, or the user invalidating
their own keys, drops their access again. Because the encryption happens
in the browser, a custodian added to a vault created outside the browser
(e.g. by import or another module) only receives a usable key once a
user holding the master key re-shares or re-encrypts the vault.
