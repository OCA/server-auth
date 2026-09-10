This modules creates a JWT validator named `demo`, and adds a
`/auth_jwt_demo/whoami` route which returns information about the
partner identified in the token.

The `whoami` endpoint can be invoked as such, assuming
[python-jose](https://pypi.org/project/python-jose/) is installed.

``` python
# /usr/bin/env python3
import time

import requests
from jose import jwt

token = jwt.encode(
    {
        "aud": "auth_jwt_test_api",
        "iss": "some issuer",
        "exp": time.time() + 60,
        "email": "mark.brown23@example.com",
    },
    key="thesecret",
    algorithm=jwt.ALGORITHMS.HS256,
)
r = requests.get(
    "http://localhost:8069/auth_jwt_demo/whoami",
    headers={"Authorization": "Bearer " + token},
)
r.raise_for_status()
print(r.json())
```
