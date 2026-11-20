# (c) 2015 ACSONE SA/NV, Dhinesh D

# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestIrConfigParameter(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.db = cls.env.cr.dbname
        cls.param_obj = cls.env["ir.config_parameter"]
        cls.data_obj = cls.env["ir.model.data"]
        cls.delay = cls.env.ref("auth_session_timeout.inactive_session_time_out_delay")

    def test_check_session_param_delay(self):
        delay = self.param_obj._auth_timeout_get_parameter_delay()
        self.assertEqual(delay, int(self.delay.value))
        self.assertIsInstance(delay, int)

    def test_check_session_param_urls(self):
        urls = self.param_obj._auth_timeout_get_parameter_ignored_urls()
        self.assertIsInstance(urls, list)


class TestIrConfigParameterCaching(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.db = self.env.cr.dbname
        self.param_obj = self.env["ir.config_parameter"]
        self.get_param_called = False
        test = self
        model_cls = type(self.param_obj)
        for name in ("get_int", "get_str"):
            orig = getattr(model_cls, name)

            def getter(*args, _orig=orig, **kwargs):
                test.get_param_called = True
                return _orig(*args, **kwargs)

            self.patch(model_cls, name, getter)

    def test_auth_timeout_get_parameter_delay_cache(self):
        """It should cache the parameter call."""
        self.get_param_called = False
        self.param_obj._auth_timeout_get_parameter_delay()
        self.assertTrue(self.get_param_called)

    def test_auth_timeout_get_parameter_ignored_urls_cache(self):
        """It should cache the parameter call."""
        self.get_param_called = False
        self.param_obj._auth_timeout_get_parameter_ignored_urls()
        self.assertTrue(self.get_param_called)

    def test_check_param_writes_clear_delay_cache(self):
        self.param_obj._auth_timeout_get_parameter_delay()
        self.get_param_called = False
        self.param_obj.set_int("inactive_session_time_out_delay", 7201)
        self.param_obj._auth_timeout_get_parameter_delay()
        self.assertTrue(self.get_param_called)

    def test_check_param_writes_clear_ignore_url_cache(self):
        self.param_obj._auth_timeout_get_parameter_ignored_urls()
        self.get_param_called = False
        self.param_obj.set_str("inactive_session_time_out_ignored_url", "example.com")
        self.param_obj._auth_timeout_get_parameter_ignored_urls()
        self.assertTrue(self.get_param_called)
