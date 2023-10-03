# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tools.config import config as odoo_config

from odoo.addons.server_environment import server_env
from odoo.addons.server_environment.tests.common import ServerEnvironmentCase


@patch.dict(odoo_config.options, {"running_env": "testing"})
class TestEnvironmentVariables(ServerEnvironmentCase):
    def test_env_variables(self):
        env_var = (
            "[auth_oauth_provider.sample]\n" "client_id=foo\n" "client_secret=bar\n"
        )
        with self.set_config_dir(None), self.set_env_variables(env_var):
            parser = server_env._load_config()
            self.assertEqual(
                list(parser.keys()), ["DEFAULT", "auth_oauth_provider.sample"]
            )
            self.assertDictEqual(
                dict(parser["auth_oauth_provider.sample"].items()),
                {
                    "client_id": "foo",
                    "client_secret": "bar",
                },
            )
