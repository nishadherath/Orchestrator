"""Public checks for Attribute metadata and nested validator state."""

import unittest

import attr


class FieldMetadataTests(unittest.TestCase):
    def test_transformer_sees_constructor_aliases(self):
        observed = []

        def record(cls, fields):
            observed.extend((field.name, field.alias, field.alias_is_default)
                            for field in fields)
            return fields

        @attr.s(auto_attribs=True, field_transformer=record)
        class Record:
            _token: str
            title: str = attr.ib(alias="display")

        self.assertEqual([("_token", "token", True),
                          ("title", "display", False)], observed)
        value = Record(token="secret", display="shown")
        self.assertEqual(("secret", "shown"), (value._token, value.title))


class ValidatorStateTests(unittest.TestCase):
    def tearDown(self):
        attr.validators.set_disabled(False)

    def test_nested_context_keeps_outer_state(self):
        self.assertFalse(attr.validators.get_disabled())
        with attr.validators.disabled():
            self.assertTrue(attr.validators.get_disabled())
            with attr.validators.disabled():
                self.assertTrue(attr.validators.get_disabled())
            self.assertTrue(attr.validators.get_disabled())
        self.assertFalse(attr.validators.get_disabled())

    def test_prior_disabled_state_is_restored(self):
        attr.validators.set_disabled(True)
        with attr.validators.disabled():
            self.assertTrue(attr.validators.get_disabled())
        self.assertTrue(attr.validators.get_disabled())


if __name__ == "__main__":
    unittest.main()
