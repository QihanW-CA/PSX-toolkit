"""Reusable mesh checks that do not depend on Blender imports."""


def is_mesh_fully_triangulated(mesh) -> bool:
    """Return whether every polygon in a mesh has exactly three vertices."""

    return all(len(polygon.vertices) == 3 for polygon in mesh.polygons)
