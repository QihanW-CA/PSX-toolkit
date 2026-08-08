"""Reusable mesh checks that do not depend on Blender imports."""

from hashlib import sha256


def _canonical_polygon(vertices: tuple[int, ...]) -> tuple[int, ...]:
    """Normalize a polygon's cyclic start and winding."""

    if not vertices:
        return vertices
    forward = tuple(
        vertices[index:] + vertices[:index] for index in range(len(vertices))
    )
    reversed_vertices = tuple(reversed(vertices))
    backward = tuple(
        reversed_vertices[index:] + reversed_vertices[:index]
        for index in range(len(reversed_vertices))
    )
    return min(forward + backward)


def is_mesh_fully_triangulated(mesh) -> bool:
    """Return whether every polygon in a mesh has exactly three vertices."""

    return all(len(polygon.vertices) == 3 for polygon in mesh.polygons)


def mesh_topology_fingerprint(mesh) -> str:
    """Return a position-independent fingerprint of indexed mesh connectivity."""

    edges = tuple(
        sorted(tuple(sorted(tuple(edge.vertices))) for edge in mesh.edges)
    )
    polygons = tuple(
        sorted(
            _canonical_polygon(tuple(polygon.vertices))
            for polygon in mesh.polygons
        )
    )
    topology = (
        len(mesh.vertices),
        len(mesh.edges),
        len(mesh.polygons),
        edges,
        polygons,
    )
    return sha256(repr(topology).encode("utf-8")).hexdigest()


def mark_mesh_prepared(settings, mesh) -> None:
    """Record approval for one exact mesh datablock and topology state."""

    settings.prepared_mesh = mesh
    settings.prepared_topology_fingerprint = mesh_topology_fingerprint(mesh)


def is_mesh_preparation_current(settings, mesh) -> bool:
    """Return whether this exact mesh still matches its prepared topology."""

    return (
        settings.prepared_mesh == mesh
        and settings.prepared_topology_fingerprint
        == mesh_topology_fingerprint(mesh)
    )


def requires_triangulation_confirmation(settings, mesh) -> bool:
    """Return whether a non-triangle mesh still needs explicit approval."""

    return (
        not is_mesh_fully_triangulated(mesh)
        and not is_mesh_preparation_current(settings, mesh)
    )
