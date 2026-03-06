from cryptography.fernet import Fernet

from odoo import fields, models
from odoo.tests.common import TransactionCase
from odoo.tools import config


class TestEncryptionModel(models.Model):
    _name = "test.encryption.model"
    _description = "Test Encryption Model"
    _inherit = ["encryption.mixin"]

    name = fields.Char()
    secret_token = fields.Char(encrypted=True)
    normal_field = fields.Char()


class TestBaseEncryptedField(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.registry.registry_invalidated = True

        TestEncryptionModel._build_model(cls.env.registry, cls.env.cr)
        cls.env.registry.setup_models(cls.env.cr)
        cls.env.registry.init_models(
            cls.env.cr, ["test.encryption.model"], dict(cls.env.context)
        )

        # Manually create table for the test model
        if not cls.env.cr._obj.closed:
            cls.env.cr.execute(
                """
                CREATE TABLE IF NOT EXISTS test_encryption_model (
                    id serial PRIMARY KEY,
                    name varchar,
                    secret_token varchar,
                    normal_field varchar,
                    create_uid int,
                    create_date timestamp,
                    write_uid int,
                    write_date timestamp
                )
            """
            )

    def setUp(self):
        super().setUp()
        self.TestModel = self.env["test.encryption.model"]
        # Reset the cached Fernet instance before each test
        from ..tools import crypto

        crypto._fernet = None
        crypto._fernet_initialized = False

        # Keep original config to restore later
        self.original_key = config.get("encryption_key")

    def tearDown(self):
        # Restore original config
        config.options["encryption_key"] = self.original_key
        # Clean up the test model table
        from ..tools import crypto

        crypto._fernet = None
        crypto._fernet_initialized = False
        super().tearDown()

    def test_01_fallback_plaintext(self):
        """Test that without a key, data is saved and read in plaintext."""
        config.options["encryption_key"] = False

        record = self.TestModel.create(
            {"name": "Fallback Test", "secret_token": "my_plaintext_secret"}
        )

        # Read from ORM
        self.assertEqual(record.secret_token, "my_plaintext_secret")

        # Verify in DB directly
        self.env.cr.execute(
            "SELECT secret_token FROM test_encryption_model WHERE id=%s", [record.id]
        )
        db_val = self.env.cr.fetchone()[0]
        self.assertEqual(
            db_val,
            "my_plaintext_secret",
            "Should be saved as plaintext in DB without a key",
        )

    def test_02_encryption_and_decryption(self):
        """Test encryption logic with a valid key."""
        key = Fernet.generate_key().decode()
        config.options["encryption_key"] = key

        record = self.TestModel.create(
            {"name": "Secure Test", "secret_token": "super_secret_123"}
        )

        # Read from ORM (should automatically decrypt via cache convert)
        self.assertEqual(record.secret_token, "super_secret_123")

        # Verify in DB directly (should be encrypted, starts with gAAAA)
        self.env.cr.execute(
            "SELECT secret_token FROM test_encryption_model WHERE id=%s", [record.id]
        )
        db_val = self.env.cr.fetchone()[0]
        self.assertNotEqual(db_val, "super_secret_123")
        self.assertTrue(db_val.startswith("gAAAA"))

        # Verify decryption works correctly outside ORM
        f = Fernet(key.encode())
        decrypted = f.decrypt(db_val.encode()).decode()
        self.assertEqual(decrypted, "super_secret_123")

    def test_03_rpc_read_masking(self):
        """Test that calling .read() masks the encrypted field with ********."""
        config.options["encryption_key"] = Fernet.generate_key().decode()

        record = self.TestModel.create(
            {"name": "RPC Test", "secret_token": "top_secret"}
        )

        # Standard ORM access is clean
        self.assertEqual(record.secret_token, "top_secret")

        # RPC/Web client .read() masks it
        res = record.read(["name", "secret_token"])[0]
        self.assertEqual(res["name"], "RPC Test")
        self.assertEqual(res["secret_token"], "********")

        # Context bypass allows reading the real dictionary if specifically requested
        res_bypassed = record.with_context(decrypt_fields=True).read(["secret_token"])[
            0
        ]
        self.assertEqual(res_bypassed["secret_token"], "top_secret")

    def test_04_dummy_write_ignored(self):
        """Test that writing the dummy value '********' does not overwrite the real secret."""
        config.options["encryption_key"] = Fernet.generate_key().decode()

        record = self.TestModel.create(
            {"name": "Dummy Ignore Test", "secret_token": "real_password"}
        )

        # Simulate frontend sending the masked password back unchanged during a write
        record.write({"name": "Updated Name", "secret_token": "********"})

        # The name should change, but the secret_token should remain 'real_password'
        self.assertEqual(record.name, "Updated Name")
        self.assertEqual(record.secret_token, "real_password")

    def test_05_dummy_create_ignored(self):
        """Test that creating with the dummy value '********' skips it."""
        config.options["encryption_key"] = Fernet.generate_key().decode()

        record = self.TestModel.create(
            {"name": "Dummy Create Test", "secret_token": "********"}
        )

        # Since it was ********, the mixin should have removed it, saving it as empty/False
        self.assertFalse(record.secret_token)
