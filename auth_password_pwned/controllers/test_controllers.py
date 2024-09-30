from odoo.http import Controller, route, Response

KNOWN_HASHES=[]


class TestRangeController(Controller):

    @route("/auth_password_pwned/range/<string:range>", type="http", auth="none")
    def test_pwned_range(self, range):
        return Response("\n".join([
            f"{k[len(range):]}:1" for k in KNOWN_HASHES if k.startswith(range)
        ]), content_type="text/plain", status=200)
