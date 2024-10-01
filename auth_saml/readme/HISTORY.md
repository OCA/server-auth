## 17.0.1.1.0

- custom message when response is too old
- avoid using werkzeug.urls method, they are deprecated
- add missing ondelete cascade when user is deleted
- attribute mapping is now also duplicated when the provider is duplicated
- factorize getting SAML attribute value, allowing using subject.nameId in mapping attributes too
- allow creating user if not found by copying a template user

## 17.0.1.0.0

Initial migration for 17.0.
