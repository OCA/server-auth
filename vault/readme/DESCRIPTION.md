This module implements a vault for secrets and files using
end-to-end-encryption. The encryption and decryption happens in the
browser using a vault specific shared master key. The master keys are
encrypted using asymmetrically. For this the user has to enter a second
password on the first login or if he needs to access data in a vault.
The asymmetric keys are stored for a certain time in the browser
storage.

The server can never access the secrets with the information available.
Only people registered in the vault can decrypt or encrypt values in a
vault. The meta data isn't encrypted to be able to search/filter for
entries more easily.

This modules requires a secure context for the browser to work properly
and therefore HTTPS support is required.

Vault Custodians can be configured in the general settings. These users
are automatically added to every newly created vault and can not be
removed from it. They keep access to the end-to-end encrypted vaults,
for example to recover the data in case an employee leaves the company.
Custodians receive read and share permissions by default; the owner can
additionally grant them write and delete permissions.

The custodian protection only applies while a user is configured as a
custodian. Removing a user from the setting, or the user invalidating
their own keys, drops their access again. Because the encryption happens
in the browser, a custodian added to a vault created outside the browser
(e.g. by import or another module) only receives a usable key once a
user holding the master key re-shares or re-encrypts the vault.

The [vault-recovery](https://github.com/fkantelberg/vault-recovery)
project focuses on disaster recovery in case of an incident to recover
secrets from old database backups or old exports.
