"""Pure helpers for validating fixed evaluated mesh topology."""

from dataclasses import dataclass

Polygon = tuple[int, ...]


def canonical_polygon(polygon: Polygon) -> Polygon:
    """Normalize cyclic start and winding while preserving vertex connectivity."""

    if not polygon:
        return polygon
    forward = tuple(
        polygon[index:] + polygon[:index] for index in range(len(polygon))
    )
    reversed_polygon = tuple(reversed(polygon))
    backward = tuple(
        reversed_polygon[index:] + reversed_polygon[:index]
        for index in range(len(reversed_polygon))
    )
    return min(forward + backward)


def canonical_polygon_topology(
    polygons: tuple[Polygon, ...],
) -> tuple[Polygon, ...]:
    """Normalize polygon representation and ignore polygon list ordering."""

    return tuple(sorted(canonical_polygon(polygon) for polygon in polygons))


@dataclass(frozen=True)
class MeshTopologySnapshot:
    """Indexed topology observed before temporary triangulation."""

    source_vertex_count: int
    source_polygons: tuple[Polygon, ...]
    evaluated_vertex_count: int
    evaluated_vertex_indices: tuple[int, ...]
    evaluated_polygons: tuple[Polygon, ...]

    @property
    def source_polygon_topology(self) -> tuple[Polygon, ...]:
        return canonical_polygon_topology(self.source_polygons)

    @property
    def evaluated_polygon_topology(self) -> tuple[Polygon, ...]:
        return canonical_polygon_topology(self.evaluated_polygons)

    @property
    def has_stable_index_sequence(self) -> bool:
        return self.evaluated_vertex_indices == tuple(
            range(self.evaluated_vertex_count)
        )
