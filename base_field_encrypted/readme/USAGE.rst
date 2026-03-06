To use the encryption capabilities in your own custom models:

1. Inherit the mixin in your model:

   .. code-block:: python

      class MyIntegration(models.Model):
          _name = 'my.integration'
          _inherit = ['encryption.mixin']

          api_secret = fields.Char(string="API Secret", encrypted=True)

2. In your XML view, use the native `password="True"` attribute so the frontend masks it:

   .. code-block:: xml

      <field name="api_secret" password="True" />

Internal Python code can access `record.api_secret` normally and will receive the
decrypted plaintext value. The web client will only receive `********`.
