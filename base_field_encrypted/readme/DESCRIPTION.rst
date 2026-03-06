This module provides a generic mixin to symmetrically encrypt data in the database
while maintaining a standard Python workflow for developers.

Odoo natively handles `password="True"` on views by sending plaintext data
to the client, where the browser masks it. This module intercepts reads and writes
to implement actual "data at rest" encryption using the `cryptography` library.
