"""Tests for generated baked-animation C data."""

import tempfile
import unittest
from pathlib import Path

from psx_toolkit.exporter.animation_model import BakedMeshAnimation
from psx_toolkit.exporter.c_animation_writer import (
    animation_output_paths,
    generate_animation_header,
    generate_animation_source,
    generate_animation_vertex_array,
    generate_source_frame_array,
    write_animation_files,
)
from psx_toolkit.exporter.model import ExportTriangle, ExportUV, ExportVertex


def _sample_animation() -> BakedMeshAnimation:
    return BakedMeshAnimation(
        mesh_name="cat_body",
        source_frames=(1, 3),
        vertex_frames=(
            (ExportVertex(1, 2, 3), ExportVertex(4, 5, 6)),
            (ExportVertex(7, 8, 9), ExportVertex(10, 11, 12)),
        ),
        uvs=(ExportUV(0, 63), ExportUV(63, 0)),
        triangles=(ExportTriangle(vertex=(0, 1, 1), uv=(0, 1, 1)),),
    )


class CAnimationWriterTests(unittest.TestCase):
    def test_flat_vertex_array_contains_frame_markers(self) -> None:
        generated = generate_animation_vertex_array(
            "cat_body_walk",
            _sample_animation(),
        )

        self.assertIn("const SVECTOR cat_body_walk_frames[]", generated)
        self.assertIn("/* Source frame 1 */", generated)
        self.assertIn("/* Source frame 3 */", generated)
        self.assertIn("{ 10, 11, 12, 0 },", generated)

    def test_source_frame_array(self) -> None:
        generated = generate_source_frame_array("cat_body_walk", (1, 3, 5))

        self.assertIn("const int32_t cat_body_walk_source_frames[]", generated)
        self.assertIn("    1,", generated)
        self.assertIn("    5,", generated)

    def test_animation_header_declarations(self) -> None:
        generated = generate_animation_header("cat_body_walk")

        self.assertIn("extern const SVECTOR cat_body_walk_frames[];", generated)
        self.assertIn("extern const uint16_t cat_body_walk_frame_count;", generated)
        self.assertIn(
            "Frame offset = frame_index * cat_body_walk_vertex_count",
            generated,
        )

    def test_animation_source_contains_static_data_and_counts(self) -> None:
        generated = generate_animation_source(
            "cat_body_walk",
            _sample_animation(),
        )

        self.assertIn("const PSXUV cat_body_walk_uvs[]", generated)
        self.assertIn("const PSXTriangle cat_body_walk_triangles[]", generated)
        self.assertIn("const uint16_t cat_body_walk_frame_count = 2;", generated)
        self.assertIn("const uint16_t cat_body_walk_vertex_count = 2;", generated)
        self.assertIn("const uint16_t cat_body_walk_triangle_count = 1;", generated)

    def test_writes_one_file_pair_per_mesh(self) -> None:
        first = _sample_animation()
        second = BakedMeshAnimation(
            mesh_name="cat_head",
            source_frames=first.source_frames,
            vertex_frames=first.vertex_frames,
            uvs=first.uvs,
            triangles=first.triangles,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = write_animation_files(
                Path(temporary_directory),
                (first, second),
                "walk",
            )

            self.assertEqual(len(paths), 4)
            self.assertTrue((Path(temporary_directory) / "walk_cat_body.c").exists())
            self.assertTrue((Path(temporary_directory) / "walk_cat_head.h").exists())

    def test_single_mesh_uses_explicit_name_for_files_and_symbols(self) -> None:
        animation = _sample_animation()

        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            paths = write_animation_files(
                directory,
                (animation,),
                "cat_body_animation",
            )

            self.assertEqual(
                tuple(path.name for path in paths),
                ("cat_body_animation.c", "cat_body_animation.h"),
            )
            source = (directory / "cat_body_animation.c").read_text()
            self.assertIn("cat_body_animation_frames[]", source)
            self.assertNotIn("cat_body_cat_body_animation", source)

    def test_single_mesh_empty_name_uses_mesh_animation_fallback(self) -> None:
        paths = animation_output_paths(Path("/output"), (_sample_animation(),), " ")

        self.assertEqual(
            tuple(path.name for path in paths),
            ("cat_body_animation.c", "cat_body_animation.h"),
        )

    def test_multiple_mesh_paths_use_explicit_root_and_mesh_suffix(self) -> None:
        first = _sample_animation()
        animations = tuple(
            BakedMeshAnimation(
                mesh_name=mesh_name,
                source_frames=first.source_frames,
                vertex_frames=first.vertex_frames,
                uvs=first.uvs,
                triangles=first.triangles,
            )
            for mesh_name in ("cat_body", "cat_head", "cat_shirt")
        )

        paths = animation_output_paths(Path("/output"), animations, "cat_walk")

        self.assertEqual(
            tuple(path.name for path in paths),
            (
                "cat_walk_cat_body.c",
                "cat_walk_cat_body.h",
                "cat_walk_cat_head.c",
                "cat_walk_cat_head.h",
                "cat_walk_cat_shirt.c",
                "cat_walk_cat_shirt.h",
            ),
        )


if __name__ == "__main__":
    unittest.main()
