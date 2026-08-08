"""Tests for C-compatible export naming."""

import unittest

from psx_toolkit.utils.naming import (
    resolve_model_output_base,
    sanitize_c_identifier,
)


class NamingTests(unittest.TestCase):
    def test_spaces_and_punctuation_become_underscores(self) -> None:
        self.assertEqual(sanitize_c_identifier("Cat Model-01"), "cat_model_01")

    def test_leading_digit_gets_a_safe_prefix(self) -> None:
        self.assertEqual(sanitize_c_identifier("01 Cat"), "model_01_cat")

    def test_empty_name_has_a_fallback(self) -> None:
        self.assertEqual(sanitize_c_identifier("---"), "model")

    def test_c_keyword_is_disambiguated(self) -> None:
        self.assertEqual(sanitize_c_identifier("static"), "static_model")

    def test_empty_model_filename_uses_mesh_fallback(self) -> None:
        self.assertEqual(
            resolve_model_output_base("cat_body", ""),
            "cat_body_model",
        )

    def test_whitespace_model_filename_uses_mesh_fallback(self) -> None:
        self.assertEqual(
            resolve_model_output_base("cat_body", "   "),
            "cat_body_model",
        )

    def test_custom_model_filename_is_complete_base(self) -> None:
        self.assertEqual(
            resolve_model_output_base("cat_body", "player_body"),
            "player_body",
        )

    def test_filename_containing_mesh_name_is_not_duplicated(self) -> None:
        self.assertEqual(
            resolve_model_output_base("cat_body", "cat_body_model"),
            "cat_body_model",
        )


if __name__ == "__main__":
    unittest.main()
