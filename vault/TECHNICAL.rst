::

  ┌───────┐ ┏━━━━━━━━━━━━━┓ ╔═══════════╗
  │ input │ ┃ unencrypted ┃ ║ encrypted ║
  └───────┘ ┗━━━━━━━━━━━━━┛ ╚═══════════╝

Vault
=====

Each vault stores entries with enrypted fields and files in a tree like structure. The access is controlled per vault. Every added user can read the secrets of a vault. Otherwise the users can receive permission to share the vault with other users, to write secrets in the vault, or to delete entries of the vault. The databases stores the public and password protected private key of each user. The password used for the private key is derived from a password entered by the user and should be different than the password used for the login. Keep in mind that the meta information like field name or file names aren't encrypted.

Shared-key encryption
=====================

To be able to securely share sensitive data between all users a shared-key encryption is used. All users share a common secret for each vault. This secret is encrypted by the public key of each user to grant access to the user by using the private key to restore the secret.

Encryption of master key
------------------------

::

  .                   ┏━━━━━━━━━━━━┓
                      ┃ Master key ┃
                      ┗━━━━━━━━━━━━┛
  ┏━━━━━━━━━━━━━━━━━┓       ┃
  ┃ User            ┃       ▼
  ┃                 ┃   ┏━━━━━━━━━┓
  ┃ ┏━━━━━━━━━━━━━┓ ┃   ┃ encrypt ┃      ╔════════════╗
  ┃ ┃ Public key  ┃━━━━▶┃ (RSA)   ┃━━━━━▶║ Master key ║
  ┃ ┗━━━━━━━━━━━━━┛ ┃   ┗━━━━━━━━━┛      ╚════════════╝
  ┃ ╔═════════════╗ ┃
  ┃ ║ Private key ║ ┃
  ┃ ╚═════════════╝ ┃
  ┗━━━━━━━━━━━━━━━━━┛

Decryption of master key
------------------------

::

  .   ┌──────────┐     ┏━━━━━━━━━━┓
      │ Password │━━━━▶┃ derive   ┃
      └──────────┘     ┃ (PBKDF2) ┃
                       ┗━━━━━━━━━━┛
                            ┃
  ┏━━━━━━━━━━━━━━━━━┓       ▼                          ╔════════════╗
  ┃ User            ┃  ┏━━━━━━━━━━┓                    ║ Master key ║
  ┃                 ┃  ┃ Password ┃                    ╚════════════╝
  ┃ ┏━━━━━━━━━━━━━┓ ┃  ┗━━━━━━━━━━┛                          ┃
  ┃ ┃ Public key  ┃ ┃       ┃                                ▼
  ┃ ┗━━━━━━━━━━━━━┛ ┃       ▼                           ┏━━━━━━━━━┓
  ┃ ╔═════════════╗ ┃   ┏━━━━━━━━┓   ┏━━━━━━━━━━━━━┓    ┃ decrypt ┃      ┏━━━━━━━━━━━━┓
  ┃ ║ Private key ║━━━━━┃ unlock ┃━━▶┃ Private key ┃━━━▶┃ (RSA)   ┃━━━━━▶┃ Master key ┃
  ┃ ╚═════════════╝ ┃   ┗━━━━━━━━┛   ┗━━━━━━━━━━━━━┛    ┗━━━━━━━━━┛      ┗━━━━━━━━━━━━┛
  ┗━━━━━━━━━━━━━━━━━┛

Symmetric encryption of the data
================================

The symmetric cipher AES is used with the common master key to encrypt/decrypt the secrets of the vaults. The encryption parameter and encrypted data is stored in the database while everything else happens in the browser.

Encryption of data
------------------

::

  .               ┏━━━━━━━━━━━━┓
                  ┃ Master key ┃
                  ┗━━━━━━━━━━━━┛
                        ┃        ┏━━━━━━━━━━━━━━━━━━┓
                        ▼        ┃ Database         ┃
                   ┏━━━━━━━━━┓   ┃                  ┃
  ┏━━━━━━━━━━━━┓   ┃ encrypt ┃   ┃╔════════════════╗┃
  ┃ Plain text ┃━━▶┃ (AES)   ┃━━━▶║ Encrypted data ║┃
  ┗━━━━━━━━━━━━┛   ┗━━━━━━━━━┛   ┃╚════════════════╝┃
                        ┃        ┃┏━━━━━━━━━━━━━━━━┓┃
                        ┗━━━━━━━━▶┃ Parameters     ┃┃
                                 ┃┗━━━━━━━━━━━━━━━━┛┃
                                 ┗━━━━━━━━━━━━━━━━━━┛

Decryption of data
------------------

::

  .                    ┏━━━━━━━━━━━━┓
                       ┃ Master key ┃
                       ┗━━━━━━━━━━━━┛
  ┏━━━━━━━━━━━━━━━━━━┓       ┃
  ┃ Database         ┃       ▼
  ┃                  ┃   ┏━━━━━━━━━┓
  ┃╔════════════════╗┃   ┃ decrypt ┃   ┏━━━━━━━━━━━━┓
  ┃║ Encrypted data ║━━━▶┃ (AES)   ┃━━▶┃ Plain text ┃
  ┃╚════════════════╝┃   ┗━━━━━━━━━┛   ┗━━━━━━━━━━━━┛
  ┃┏━━━━━━━━━━━━━━━━┓┃       ▲
  ┃┃ Parameters     ┃━━━━━━━━┛
  ┃┗━━━━━━━━━━━━━━━━┛┃
  ┗━━━━━━━━━━━━━━━━━━┛

Inbox
=====

This allows an user to receive encrypted secrets by external or internal Odoo users. External users have to use either the owner specific inbox link from his preferences or the link of an already created inbox. The value is symmetrically encrypted. The key for the encryption is wrapped with the public key of the user of the inbox to grant the user the access to the key. Internal users can directly send a secret from a vault entry to another user who has enabled this feature. If a direct link is used the access counter and expiration time can block an overwrite.

Encryption of inbox
-------------------

::

  .                   ┏━━━━━━━━━━━━┓
                      ┃ Plain data ┃
                      ┗━━━━━━━━━━━━┛
  ┏━━━━━━━━━━━━━━━━━┓       ┃
  ┃ User            ┃       ▼
  ┃                 ┃   ┏━━━━━━━━━┓
  ┃ ┏━━━━━━━━━━━━━┓ ┃   ┃ encrypt ┃      ╔════════════════╗
  ┃ ┃ Public key  ┃━━━━▶┃ (RSA)   ┃━━━━━▶║ Encrypted data ║
  ┃ ┗━━━━━━━━━━━━━┛ ┃   ┗━━━━━━━━━┛      ╚════════════════╝
  ┃ ╔═════════════╗ ┃
  ┃ ║ Private key ║ ┃
  ┃ ╚═════════════╝ ┃
  ┗━━━━━━━━━━━━━━━━━┛

Decryption of inbox
-------------------

::

  .   ┌──────────┐     ┏━━━━━━━━━━┓
      │ Password │━━━━▶┃ derive   ┃
      └──────────┘     ┃ (PBKDF2) ┃
                       ┗━━━━━━━━━━┛
                            ┃
  ┏━━━━━━━━━━━━━━━━━┓       ▼                        ╔════════════════╗
  ┃ User            ┃  ┏━━━━━━━━━━┓                  ║ Encrypted data ║
  ┃                 ┃  ┃ Password ┃                  ╚════════════════╝
  ┃ ┏━━━━━━━━━━━━━┓ ┃  ┗━━━━━━━━━━┛                          ┃
  ┃ ┃ Public key  ┃ ┃       ┃                                ▼
  ┃ ┗━━━━━━━━━━━━━┛ ┃       ▼                           ┏━━━━━━━━━┓
  ┃ ╔═════════════╗ ┃   ┏━━━━━━━━┓   ┏━━━━━━━━━━━━━┓    ┃ decrypt ┃      ┏━━━━━━━━━━━━┓
  ┃ ║ Private key ║━━━━━┃ unlock ┃━━▶┃ Private key ┃━━━▶┃ (RSA)   ┃━━━━━▶┃ Plain data ┃
  ┃ ╚═════════════╝ ┃   ┗━━━━━━━━┛   ┗━━━━━━━━━━━━━┛    ┗━━━━━━━━━┛      ┗━━━━━━━━━━━━┛
  ┗━━━━━━━━━━━━━━━━━┛
