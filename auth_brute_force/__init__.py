import time
from unittest import TestCase

from odoo.http import _request_stack
from odoo.tools import DotDict

from . import models


def setUp(self):
    fake_req = DotDict(
        {
            # various things go and access request items
            "httprequest": DotDict(
                {
                    "environ": {
                        "REMOTE_ADDR": "127.0.0.1",
                        "HTTP_REFERER": "referer",
                        "HTTP_USER_AGENT": "user agent",
                        "HTTP_ACCEPT_LANGUAGE": "Language",
                    },
                    "cookies": {},
                }
            ),
            # bypass check_identity flow
            "session": {"identity-check-last": time.time()},
        }
    )
    _request_stack.push(fake_req)
    self.addCleanup(_request_stack.pop)


TestCase.setUp = setUp
