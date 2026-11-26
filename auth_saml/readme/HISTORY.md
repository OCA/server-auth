## 18.0.1.2.1 (2026-11-26)

### Bugfixes

- Ensure that autoredirect keeps URL that was displayed before login.


## 18.0.1.2.0 (2026-11-26)

### Features

- Allow configuring a requested authentication context (`RequestedAuthnContext`)
  per SAML provider. This helps with IDPs, such as Microsoft Entra ID or ADFS,
  that otherwise return an empty `AuthnContext` that pysaml2 rejects. ([#1020](https://github.com/OCA/server-auth/issues/1020))


## 18.0.1.1.3 (2026-06-18)

### Bugfixes

- Fix sending a mail when configuring SAML for a user.


## 18.0.1.0.3 (2025-09-11)

### Features

- When using attribute mapping, only write value that changes.
  Not writing the value systematically avoids getting security mail on login/email
  when there is no real change.


## 18.0.1.0.2 (2025-05-13)

### Bugfixes

- Avoid redirecting when there is a SAML error.


## 18.0.1.0.0

Initial migration for 18.0.
