"""Tests for canonical pre-triangulation topology validation."""

import unittest

from psx_toolkit.exporter.animation_model import validate_animation_topology
from psx_toolkit.exporter.topology_diagnostics import (
    MeshTopologySnapshot,
    canonical_polygon,
    canonical_polygon_topology,
)


def _snapshot(polygons) -> MeshTopologySnapshot:
    vertex_count = 6
    return MeshTopologySnapshot(
        source_vertex_count=vertex_count,
        source_polygons=polygons,
        evaluated_vertex_count=vertex_count,
        evaluated_vertex_indices=tuple(range(vertex_count)),
        evaluated_polygons=polygons,
    )


class TopologyDiagnosticTests(unittest.TestCase):
    def test_cyclic_polygon_vertex_order_is_equivalent(self) -> None:
        self.assertEqual(
            canonical_polygon((1, 2, 3, 4)),
            canonical_polygon((3, 4, 1, 2)),
        )

    def test_reversed_polygon_winding_is_equivalent(self) -> None:
        self.assertEqual(
            canonical_polygon((1, 2, 3, 4)),
            canonical_polygon((4, 3, 2, 1)),
        )

    def test_polygon_list_order_is_ignored(self) -> None:
        first = ((0, 1, 2), (2, 3, 4, 5))
        reordered = ((4, 5, 2, 3), (1, 2, 0))

        self.assertEqual(
            canonical_polygon_topology(first),
            canonical_polygon_topology(reordered),
        )
        validate_animation_topology(
            "cat", 11, _snapshot(first), _snapshot(reordered)
        )

    def test_triangle_array_order_is_not_part_of_frame_validation(self) -> None:
        topology = _snapshot(((0, 1, 2), (2, 3, 4)))
        reference_triangles = ((0, 1, 2), (2, 3, 4))
        independently_ordered = ((4, 2, 3), (1, 2, 0))

        self.assertNotEqual(reference_triangles, independently_ordered)
        validate_animation_topology("cat", 11, topology, topology)

    def test_deforming_quad_diagonal_is_not_compared(self) -> None:
        topology = _snapshot(((0, 1, 2, 3),))
        reference_split = ((0, 1, 2), (0, 2, 3))
        hypothetical_later_split = ((0, 1, 3), (1, 2, 3))

        self.assertNotEqual(reference_split, hypothetical_later_split)
        validate_animation_topology("cat", 11, topology, topology)

    def test_genuine_connectivity_change_is_not_equivalent(self) -> None:
        reference = ((0, 1, 2), (2, 3, 4))
        changed = ((0, 1, 3), (2, 3, 4))

        self.assertNotEqual(
            canonical_polygon_topology(reference),
            canonical_polygon_topology(changed),
        )


if __name__ == "__main__":
    unittest.main()
