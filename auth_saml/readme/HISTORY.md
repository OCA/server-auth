## 17.0.1.1.0 (2026-06-18)

### Features

- - custom message when response is too old
  - avoid using werkzeug.urls method, they are deprecated
  - add missing ondelete cascade when user is deleted
  - attribute mapping is now also duplicated when the provider is duplicated
  - factorize getting SAML attribute value, allowing using subject.nameId in mapping attributes too
  - allow creating user if not found by copying a template user, or activating a deactivated user.


## 17.0.1.0.5 (2026-06-18)

### Bugfixes

- Fix sending a mail when configuring SAML for a user.


## 17.0.1.0.2 (2025-05-13)

### Bugfixes

- Avoid redirecting when there is a SAML error.


## 17.0.1.0.1

When using attribute mapping, only write value that changes.
No writing the value systematically avoids getting security mail on login/email
when there is no real change.

## 17.0.1.0.0

Initial migration for 17.0.
