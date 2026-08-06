"""Tests for dimension-aware loop UV conversion and deduplication."""

import unittest

from psx_toolkit.exporter.model import ExportUV
from psx_toolkit.exporter.uv_conversion import convert_uv, deduplicate_uvs


class UVConversionTests(unittest.TestCase):
    def test_64_by_64_uv_conversion(self) -> None:
        converted = convert_uv(0.25, 0.75, 64, 64, flip_v=True)

        self.assertEqual(converted, ExportUV(16, 16))

    def test_128_by_64_uv_conversion(self) -> None:
        converted = convert_uv(0.5, 0.5, 128, 64, flip_v=True)

        self.assertEqual(converted, ExportUV(64, 32))

    def test_256_by_256_uv_conversion(self) -> None:
        converted = convert_uv(1.0, 0.0, 256, 256, flip_v=True)

        self.assertEqual(converted, ExportUV(255, 255))

    def test_flip_v_enabled(self) -> None:
        converted = convert_uv(0.0, 0.25, 64, 64, flip_v=True)

        self.assertEqual(converted.v, 47)

    def test_flip_v_disabled(self) -> None:
        converted = convert_uv(0.0, 0.25, 64, 64, flip_v=False)

        self.assertEqual(converted.v, 16)

    def test_zero_and_one_uv_values(self) -> None:
        self.assertEqual(
            convert_uv(0.0, 0.0, 64, 64, flip_v=False),
            ExportUV(0, 0),
        )
        self.assertEqual(
            convert_uv(1.0, 1.0, 64, 64, flip_v=False),
            ExportUV(63, 63),
        )

    def test_uv_conversion_clamps_to_texture_bounds(self) -> None:
        self.assertEqual(
            convert_uv(-1.0, 2.0, 128, 64, flip_v=False),
            ExportUV(0, 63),
        )
        self.assertEqual(
            convert_uv(2.0, -1.0, 128, 64, flip_v=False),
            ExportUV(127, 0),
        )

    def test_uv_deduplication_preserves_corner_indices(self) -> None:
        first = ExportUV(0, 63)
        second = ExportUV(127, 0)

        unique, indices = deduplicate_uvs((first, second, first, second))

        self.assertEqual(unique, (first, second))
        self.assertEqual(indices, (0, 1, 0, 1))


if __name__ == "__main__":
    unittest.main()
