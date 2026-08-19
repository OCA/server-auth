from odoo.tests.common import TransactionCase


class TestAuthSamlModelsSamlAttributeMapping(TransactionCase):
    def setUp(self):
        super().setUp()
        self.SamlAttributeMapping = self.env["auth.saml.attribute.mapping"]

    def test_field_name_selection(self):
        # Call the method
        field_name_selection = self.SamlAttributeMapping._field_name_selection()

        # Fetch all user fields
        user_fields = self.env["res.users"].fields_get().items()

        # Filter out valid fields (char and not readonly)
        valid_fields = [
            (f, d.get("string"))
            for f, d in user_fields
            if d.get("type") == "char" and not d.get("readonly")
        ]

        # Sort the valid fields by their name
        valid_fields.sort(key=lambda r: r[1])

        # Assert that the selections match the valid fields
        self.assertEqual(field_name_selection, valid_fields)
