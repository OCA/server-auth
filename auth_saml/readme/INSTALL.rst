This addon requires the python module ``pysaml2``.

``pysaml2`` requires the binary ``xmlsec1`` (on Debian or Ubuntu you can install it with ``apt-get install xmlsec1``)

When following the requirements.txt from odoo, the cryptography module must not be the latest version, otherwise it is incompatible with pyopenssl 19.
This is necessary because old cryptography/pyopenssl don't declare minimum supported versions.
It is possible to use newer version of those libraries, eventually patching the Odoo core to stay compatible.
As this issue is not related to this module, nothing is enforced at the module level.
