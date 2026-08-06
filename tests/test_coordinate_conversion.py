"""Tests for Blender-to-PS1 coordinate conversion."""

import unittest

from psx_toolkit.exporter.coordinate_conversion import (
    CoordinateOverflowError,
    convert_position,
    position_for_coordinate_space,
)
from psx_toolkit.exporter.model import ExportVertex


class CoordinateConversionTests(unittest.TestCase):
    def test_local_space_does_not_apply_world_matrix(self) -> None:
        class TrackingMatrix:
            was_applied = False

            def __matmul__(self, position):
                self.was_applied = True
                return (9.0, 9.0, 9.0)

        local_position = [1.0, 2.0, 3.0]
        matrix = TrackingMatrix()

        result = position_for_coordinate_space(local_position, matrix, "LOCAL")

        self.assertEqual(result, local_position)
        self.assertIsNot(result, local_position)
        self.assertFalse(matrix.was_applied)

    def test_world_space_applies_world_matrix(self) -> None:
        class TranslationMatrix:
            def __matmul__(self, position):
                return tuple(value + 10.0 for value in position)

        result = position_for_coordinate_space(
            [1.0, 2.0, 3.0],
            TranslationMatrix(),
            "WORLD",
        )

        self.assertEqual(result, (11.0, 12.0, 13.0))

    def test_axis_conversion(self) -> None:
        converted = convert_position((1.0, 2.0, 3.0), 1.0, vertex_index=0)

        self.assertEqual(converted, ExportVertex(1, -3, 2))

    def test_positive_blender_z_becomes_negative_ps1_y(self) -> None:
        converted = convert_position((0.0, 0.0, 4.0), 1.0, vertex_index=0)

        self.assertEqual(converted.y, -4)

    def test_negative_blender_z_becomes_positive_ps1_y(self) -> None:
        converted = convert_position((0.0, 0.0, -4.0), 1.0, vertex_index=0)

        self.assertEqual(converted.y, 4)

    def test_scaling_and_rounding(self) -> None:
        converted = convert_position(
            (0.5, -0.25, 1.25),
            256.0,
            vertex_index=4,
        )

        self.assertEqual(converted, ExportVertex(128, -320, -64))

    def test_coordinate_overflow_identifies_vertex(self) -> None:
        with self.assertRaisesRegex(CoordinateOverflowError, "Vertex 7"):
            convert_position((128.0, 0.0, 0.0), 256.0, vertex_index=7)


if __name__ == "__main__":
    unittest.main()
