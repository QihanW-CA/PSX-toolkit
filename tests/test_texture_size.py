"""Tests for texture-size source resolution and validation."""

import unittest
from types import SimpleNamespace

from psx_toolkit.exporter.texture_size import (
    TextureSizeError,
    resolve_texture_size,
)


class TextureSizeTests(unittest.TestCase):
    def test_manual_texture_size(self) -> None:
        settings = SimpleNamespace(
            texture_size_source="MANUAL",
            texture_width=128,
            texture_height=64,
        )

        self.assertEqual(resolve_texture_size(settings), (128, 64))

    def test_material_texture_size(self) -> None:
        settings = SimpleNamespace(
            texture_size_source="MATERIAL",
            texture_image=SimpleNamespace(size=(64, 64)),
        )

        self.assertEqual(resolve_texture_size(settings), (64, 64))

    def test_material_mode_requires_an_image(self) -> None:
        settings = SimpleNamespace(
            texture_size_source="MATERIAL",
            texture_image=None,
        )

        with self.assertRaisesRegex(TextureSizeError, "Select a texture image"):
            resolve_texture_size(settings)

    def test_invalid_manual_dimensions(self) -> None:
        invalid_sizes = ((0, 64), (64, 0), (257, 64), (64, 257))

        for width, height in invalid_sizes:
            with self.subTest(width=width, height=height):
                settings = SimpleNamespace(
                    texture_size_source="MANUAL",
                    texture_width=width,
                    texture_height=height,
                )
                with self.assertRaises(TextureSizeError):
                    resolve_texture_size(settings)


if __name__ == "__main__":
    unittest.main()
