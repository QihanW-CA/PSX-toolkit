"""Tests for mesh preparation topology fingerprints."""

import unittest

from psx_toolkit.utils.mesh_validation import (
    is_mesh_preparation_current,
    mark_mesh_prepared,
    mesh_topology_fingerprint,
    requires_triangulation_confirmation,
)


class _Element:
    def __init__(self, vertices=(), position=None):
        self.vertices = vertices
        self.position = position


class _Mesh:
    def __init__(self, *, vertex_count=4, edges=None, polygons=None):
        self.vertices = [
            _Element(position=(index, 0, 0)) for index in range(vertex_count)
        ]
        self.edges = [
            _Element(edge)
            for edge in (
                edges
                if edges is not None
                else ((0, 1), (1, 2), (2, 3), (0, 3))
            )
        ]
        self.polygons = [
            _Element(polygon)
            for polygon in (polygons if polygons is not None else ((0, 1, 2, 3),))
        ]


class _Settings:
    prepared_mesh = None
    prepared_topology_fingerprint = ""


class MeshPreparationTests(unittest.TestCase):
    def test_unprepared_non_triangle_mesh_requires_confirmation(self) -> None:
        self.assertTrue(requires_triangulation_confirmation(_Settings(), _Mesh()))

    def test_prepared_unchanged_mesh_skips_duplicate_confirmation(self) -> None:
        settings = _Settings()
        mesh = _Mesh()

        mark_mesh_prepared(settings, mesh)

        self.assertTrue(is_mesh_preparation_current(settings, mesh))
        self.assertFalse(requires_triangulation_confirmation(settings, mesh))

    def test_topology_edit_invalidates_preparation(self) -> None:
        settings = _Settings()
        mesh = _Mesh()
        mark_mesh_prepared(settings, mesh)

        mesh.edges.append(_Element((0, 2)))

        self.assertFalse(is_mesh_preparation_current(settings, mesh))
        self.assertTrue(requires_triangulation_confirmation(settings, mesh))

    def test_different_mesh_does_not_inherit_preparation(self) -> None:
        settings = _Settings()
        prepared_mesh = _Mesh()
        other_mesh = _Mesh()
        mark_mesh_prepared(settings, prepared_mesh)

        self.assertFalse(is_mesh_preparation_current(settings, other_mesh))
        self.assertTrue(
            requires_triangulation_confirmation(settings, other_mesh)
        )

    def test_vertex_position_change_does_not_invalidate_preparation(self) -> None:
        settings = _Settings()
        mesh = _Mesh()
        mark_mesh_prepared(settings, mesh)

        mesh.vertices[0].position = (100, 200, 300)

        self.assertTrue(is_mesh_preparation_current(settings, mesh))

    def test_fingerprint_does_not_modify_source_topology(self) -> None:
        mesh = _Mesh()
        original_edges = tuple(element.vertices for element in mesh.edges)
        original_polygons = tuple(element.vertices for element in mesh.polygons)

        mesh_topology_fingerprint(mesh)

        self.assertEqual(
            tuple(element.vertices for element in mesh.edges), original_edges
        )
        self.assertEqual(
            tuple(element.vertices for element in mesh.polygons),
            original_polygons,
        )


if __name__ == "__main__":
    unittest.main()
