"""Tests for static model C and header generation."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from psx_toolkit.exporter.c_writer import (
    generate_header,
    generate_source,
    generate_triangle_array,
    generate_uv_array,
    generate_vertex_array,
    make_include_guard,
    write_model_files,
)
from psx_toolkit.exporter.model import (
    ExportMesh,
    ExportTriangle,
    ExportUV,
    ExportVertex,
)
from psx_toolkit.utils.naming import resolve_model_output_base


def _sample_mesh() -> ExportMesh:
    return ExportMesh(
        vertices=(
            ExportVertex(-256, 0, 256),
            ExportVertex(256, 0, 256),
            ExportVertex(0, 256, -256),
        ),
        uvs=(ExportUV(0, 255), ExportUV(255, 255), ExportUV(128, 0)),
        triangles=(ExportTriangle(vertex=(0, 1, 2), uv=(0, 1, 2)),),
    )


class CWriterTests(unittest.TestCase):
    def test_include_guard_generation(self) -> None:
        self.assertEqual(make_include_guard("cat_model"), "CAT_MODEL_H")

    def test_header_generation(self) -> None:
        header = generate_header("cat_model")

        self.assertIn("#include <psxgte.h>", header)
        self.assertIn("extern const SVECTOR cat_model_vertices[];", header)
        self.assertIn("extern const PSXUV cat_model_uvs[];", header)
        self.assertIn("extern const PSXTriangle cat_model_triangles[];", header)
        self.assertIn("extern const uint16_t cat_model_uv_count;", header)
        self.assertNotIn("animation", header)

    def test_vertex_array_generation(self) -> None:
        generated = generate_vertex_array("cat_model", _sample_mesh().vertices)

        self.assertIn("const SVECTOR cat_model_vertices[]", generated)
        self.assertIn("{ -256, 0, 256, 0 },", generated)
        self.assertIn("{ 0, 256, -256, 0 },", generated)

    def test_uv_array_generation(self) -> None:
        generated = generate_uv_array("cat_model", _sample_mesh().uvs)

        self.assertIn("const PSXUV cat_model_uvs[]", generated)
        self.assertIn("{ 0, 255 },", generated)
        self.assertIn("{ 128, 0 },", generated)

    def test_triangle_array_generation(self) -> None:
        generated = generate_triangle_array(
            "cat_model",
            _sample_mesh().triangles,
        )

        self.assertIn("const PSXTriangle cat_model_triangles[]", generated)
        self.assertIn("{ { 0, 1, 2 }, { 0, 1, 2 } },", generated)

    def test_source_contains_real_counts(self) -> None:
        source = generate_source("cat_model", _sample_mesh())

        self.assertIn("const uint16_t cat_model_vertex_count = 3;", source)
        self.assertIn("const uint16_t cat_model_uv_count = 3;", source)
        self.assertIn("const uint16_t cat_model_triangle_count = 1;", source)

    def test_failed_second_replacement_rolls_back_first_file(self) -> None:
        real_replace = os.replace
        replace_count = 0

        def fail_second_replace(source, target):
            nonlocal replace_count
            replace_count += 1
            if replace_count == 2:
                raise OSError("simulated replacement failure")
            return real_replace(source, target)

        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            with patch(
                "psx_toolkit.exporter.c_writer.os.replace",
                side_effect=fail_second_replace,
            ):
                with self.assertRaises(OSError):
                    write_model_files(directory, "cat_model", _sample_mesh())

            self.assertFalse((directory / "cat_model.c").exists())
            self.assertFalse((directory / "cat_model.h").exists())

    def test_overwrite_protection_uses_resolved_model_filename(self) -> None:
        symbol_base = resolve_model_output_base("cat_body", "player_body")

        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            write_model_files(directory, symbol_base, _sample_mesh())

            with self.assertRaises(FileExistsError):
                write_model_files(directory, symbol_base, _sample_mesh())

            self.assertTrue((directory / "player_body.c").exists())
            self.assertTrue((directory / "player_body.h").exists())


if __name__ == "__main__":
    unittest.main()
