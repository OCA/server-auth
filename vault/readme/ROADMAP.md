- Field and file history for restoration
- Import improvement

> - Support challenge-response/FIDO2
> - Support for argon2 and kdbx v4

- When changing an entry from one vault to another existing vault, the
  values added on this entry cannot be accessed, so the field vault is
  going to be readonly when it is defined.

  If you want to move entries between vaults you can use the export -\>
  import option.

- HTTPS or localhost (secure browser context) is required for the client
  side encryption
