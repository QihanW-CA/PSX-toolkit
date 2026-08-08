"""Tests for baked animation ranges, naming, and frame layout."""

import unittest

from psx_toolkit.exporter.animation_model import (
    AnimationTopologyError,
    BakedMeshAnimation,
    flatten_vertex_frames,
    resolve_animation_output_bases,
    sampled_frame_range,
    validate_animation_topology,
)
from psx_toolkit.exporter.model import ExportTriangle, ExportUV, ExportVertex
from psx_toolkit.exporter.topology_diagnostics import MeshTopologySnapshot


def _topology(
    *,
    vertex_count=4,
    polygons=((0, 1, 2, 3),),
    vertex_indices=None,
) -> MeshTopologySnapshot:
    if vertex_indices is None:
        vertex_indices = tuple(range(vertex_count))
    return MeshTopologySnapshot(
        source_vertex_count=vertex_count,
        source_polygons=polygons,
        evaluated_vertex_count=vertex_count,
        evaluated_vertex_indices=vertex_indices,
        evaluated_polygons=polygons,
)


def _sample_animation() -> BakedMeshAnimation:
    return BakedMeshAnimation(
        mesh_name="Cat Body",
        source_frames=(1, 3),
        vertex_frames=(
            (ExportVertex(1, 2, 3), ExportVertex(4, 5, 6)),
            (ExportVertex(7, 8, 9), ExportVertex(10, 11, 12)),
        ),
        uvs=(ExportUV(0, 0),),
        triangles=(ExportTriangle(vertex=(0, 1, 1), uv=(0, 0, 0)),),
    )


class AnimationModelTests(unittest.TestCase):
    def test_inclusive_frame_range(self) -> None:
        self.assertEqual(sampled_frame_range(1, 4, 1), (1, 2, 3, 4))

    def test_frame_step_stops_before_unhit_end(self) -> None:
        self.assertEqual(sampled_frame_range(1, 10, 2), (1, 3, 5, 7, 9))

    def test_invalid_frame_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "start frame"):
            sampled_frame_range(10, 1, 1)
        with self.assertRaisesRegex(ValueError, "step"):
            sampled_frame_range(1, 10, 0)

    def test_single_mesh_explicit_animation_name_is_complete_base(self) -> None:
        self.assertEqual(
            resolve_animation_output_bases(
                ("cat_body",),
                "cat_body_animation",
            ),
            ("cat_body_animation",),
        )

    def test_single_mesh_unrelated_animation_name_is_complete_base(self) -> None:
        self.assertEqual(
            resolve_animation_output_bases(("cat_body",), "walk_cycle"),
            ("walk_cycle",),
        )

    def test_empty_animation_name_uses_mesh_fallback(self) -> None:
        self.assertEqual(
            resolve_animation_output_bases(("cat_body",), "   "),
            ("cat_body_animation",),
        )

    def test_multiple_meshes_append_mesh_to_explicit_root(self) -> None:
        self.assertEqual(
            resolve_animation_output_bases(
                ("cat_body", "cat_head", "cat_shirt"),
                "cat_walk",
            ),
            (
                "cat_walk_cat_body",
                "cat_walk_cat_head",
                "cat_walk_cat_shirt",
            ),
        )

    def test_frame_count_and_vertex_count(self) -> None:
        animation = _sample_animation()

        self.assertEqual(animation.frame_count, 2)
        self.assertEqual(animation.vertex_count, 2)
        self.assertEqual(len(animation.triangles), 1)
        self.assertEqual(len(animation.uvs), 1)

    def test_flattened_vertices_are_frame_major(self) -> None:
        animation = _sample_animation()

        self.assertEqual(
            flatten_vertex_frames(animation.vertex_frames),
            (
                ExportVertex(1, 2, 3),
                ExportVertex(4, 5, 6),
                ExportVertex(7, 8, 9),
                ExportVertex(10, 11, 12),
            ),
        )

    def test_topology_validation_accepts_deformation(self) -> None:
        reference = _topology()

        validate_animation_topology("cat", 2, reference, reference)

    def test_topology_validation_rejects_vertex_count_change(self) -> None:
        reference = _topology()
        changed = _topology(vertex_count=5, polygons=((0, 1, 2, 3),))

        with self.assertRaisesRegex(AnimationTopologyError, "frame 4"):
            validate_animation_topology("cat", 4, reference, changed)

    def test_topology_validation_rejects_polygon_count_change(self) -> None:
        reference = _topology()
        changed = _topology(polygons=((0, 1, 2), (0, 2, 3)))

        with self.assertRaisesRegex(AnimationTopologyError, "polygon count"):
            validate_animation_topology("cat", 3, reference, changed)

    def test_topology_validation_rejects_connectivity_change(self) -> None:
        reference = _topology(polygons=((0, 1, 2), (0, 2, 3)))
        changed = _topology(polygons=((0, 1, 3), (1, 2, 3)))

        with self.assertRaisesRegex(AnimationTopologyError, "polygon topology"):
            validate_animation_topology("cat", 3, reference, changed)

    def test_topology_validation_rejects_unstable_vertex_indices(self) -> None:
        reference = _topology()
        changed = _topology(vertex_indices=(1, 0, 2, 3))

        with self.assertRaisesRegex(AnimationTopologyError, "stable vertex indices"):
            validate_animation_topology("cat", 3, reference, changed)

    def test_animation_rejects_incomplete_vertex_frame(self) -> None:
        with self.assertRaisesRegex(ValueError, "reference vertex count"):
            BakedMeshAnimation(
                mesh_name="cat",
                source_frames=(1, 2),
                vertex_frames=(
                    (ExportVertex(0, 0, 0), ExportVertex(1, 1, 1)),
                    (ExportVertex(2, 2, 2),),
                ),
                uvs=(ExportUV(0, 0),),
                triangles=(
                    ExportTriangle(vertex=(0, 1, 1), uv=(0, 0, 0)),
                ),
            )


if __name__ == "__main__":
    unittest.main()
