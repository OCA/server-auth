This module implements a vault for secrets and files using end-to-end-encryption. The encryption and decryption happens in the browser using a vault specific shared master key. The master keys are encrypted using asymmetrically. For this the user has to enter a second password on the first login or if he needs to access data in a vault. The asymmetric keys are stored for a certain time in the browser storage.

The server can never access the secrets with the information available. Only people registered in the vault can decrypt or encrypt values in a vault. The meta data isn't encrypted to be able to search/filter for entries more easily.

This modules requires a secure context for the browser to work properly.

The `vault-recovery <https://github.com/fkantelberg/vault-recovery>`_ project focuses on disaster recovery in case of an incident to recover secrets from old database backups or old exports.
