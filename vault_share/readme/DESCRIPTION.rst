This module implements possibilities to share specific secrets with external users. This bases on the vault implementation and the generated RSA key pair.

Share
=====

This allows an user to share a secret with external users. A share can be generated from a vault entry or directly created by an user. The secret is symmetrically encrypted by a key derived from a pin. To grant access the user has to transmit the link and pin with the external. If either the access counter reaches 0 or the share expires it will be deleted automatically. Due to the usage of a numeric pin and the browser side decryption a share is vulnerable to brute-force attacks and shouldn't be used as a permanent storage for secrets. For long time uses the user should create an account and a vault should be used.
