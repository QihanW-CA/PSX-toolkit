"""Extract a static export model from a Blender evaluated temporary mesh."""

import bmesh

from .coordinate_conversion import (
    CoordinateOverflowError,
    convert_position,
    position_for_coordinate_space,
)
from .model import ExportMesh, ExportTriangle, ExportVertex
from .topology_diagnostics import MeshTopologySnapshot
from .uv_conversion import convert_uv, deduplicate_uvs

UINT16_MAX = 65535


class MeshExtractionError(ValueError):
    """Raised when Blender mesh data cannot produce a valid static export."""


def _triangulate_temporary_mesh(mesh) -> None:
    temporary_bmesh = bmesh.new()
    try:
        temporary_bmesh.from_mesh(mesh)
        bmesh.ops.triangulate(
            temporary_bmesh,
            faces=list(temporary_bmesh.faces),
        )
        temporary_bmesh.to_mesh(mesh)
        mesh.update()
    except Exception as error:
        raise MeshExtractionError(
            f"Temporary triangulation failed: {error}"
        ) from error
    finally:
        temporary_bmesh.free()

    if not all(len(polygon.vertices) == 3 for polygon in mesh.polygons):
        raise MeshExtractionError(
            "Temporary triangulation produced non-triangle faces."
        )


def _extract_mesh_data(
    mesh,
    matrix_world,
    scale: float,
    coordinate_space: str,
    texture_width: int,
    texture_height: int,
    flip_v: bool,
) -> ExportMesh:
    if not mesh.vertices or not mesh.polygons:
        raise MeshExtractionError("The selected mesh is empty.")

    uv_layer = mesh.uv_layers.active
    if uv_layer is None:
        raise MeshExtractionError("The selected mesh has no active UV layer.")

    vertices = _extract_vertex_positions(
        mesh,
        matrix_world,
        scale,
        coordinate_space,
    )
    if len(mesh.polygons) > UINT16_MAX:
        raise MeshExtractionError("Triangle count exceeds the uint16_t limit of 65535.")

    triangle_vertices: list[tuple[int, int, int]] = []
    corner_uvs = []
    for polygon in mesh.polygons:
        vertex_indices = tuple(polygon.vertices)
        if len(vertex_indices) != 3:
            raise MeshExtractionError(
                f"Polygon {polygon.index} was not triangulated successfully."
            )
        if any(index < 0 or index > UINT16_MAX for index in vertex_indices):
            raise MeshExtractionError(
                f"Polygon {polygon.index} contains a vertex index outside uint16_t."
            )

        triangle_vertices.append(vertex_indices)
        for loop_index in polygon.loop_indices:
            loop_uv = uv_layer.data[loop_index].uv
            corner_uvs.append(
                convert_uv(
                    loop_uv.x,
                    loop_uv.y,
                    texture_width,
                    texture_height,
                    flip_v=flip_v,
                )
            )

    unique_uvs, uv_indices = deduplicate_uvs(corner_uvs)
    if len(unique_uvs) > UINT16_MAX:
        raise MeshExtractionError("UV count exceeds the uint16_t limit of 65535.")

    triangles = tuple(
        ExportTriangle(
            vertex=vertex_indices,
            uv=(
                uv_indices[index * 3],
                uv_indices[index * 3 + 1],
                uv_indices[index * 3 + 2],
            ),
        )
        for index, vertex_indices in enumerate(triangle_vertices)
    )
    return ExportMesh(
        vertices=tuple(vertices),
        uvs=unique_uvs,
        triangles=triangles,
    )


def _extract_vertex_positions(
    mesh,
    matrix_world,
    scale: float,
    coordinate_space: str,
) -> tuple[ExportVertex, ...]:
    """Convert positions while preserving Blender's evaluated vertex index order."""

    if len(mesh.vertices) > UINT16_MAX:
        raise MeshExtractionError("Vertex count exceeds the uint16_t limit of 65535.")

    vertices = []
    for expected_index, vertex in enumerate(mesh.vertices):
        if vertex.index != expected_index:
            raise MeshExtractionError(
                "Evaluated mesh does not provide a stable contiguous vertex "
                "index sequence."
            )
        export_position = position_for_coordinate_space(
            vertex.co,
            matrix_world,
            coordinate_space,
        )
        try:
            vertices.append(
                convert_position(
                    export_position,
                    scale,
                    vertex_index=vertex.index,
                )
            )
        except CoordinateOverflowError as error:
            raise MeshExtractionError(str(error)) from error
    return tuple(vertices)


def _polygon_topology(mesh) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(polygon.vertices) for polygon in mesh.polygons)


def _topology_snapshot(source_mesh, evaluated_mesh) -> MeshTopologySnapshot:
    return MeshTopologySnapshot(
        source_vertex_count=len(source_mesh.vertices),
        source_polygons=_polygon_topology(source_mesh),
        evaluated_vertex_count=len(evaluated_mesh.vertices),
        evaluated_vertex_indices=tuple(
            vertex.index for vertex in evaluated_mesh.vertices
        ),
        evaluated_polygons=_polygon_topology(evaluated_mesh),
    )


def extract_evaluated_mesh_with_topology(
    context,
    source_object,
    scale: float,
    coordinate_space: str,
    texture_width: int,
    texture_height: int,
    flip_v: bool,
) -> tuple[ExportMesh, MeshTopologySnapshot]:
    """Extract a mesh plus diagnostic topology and release its temporary copy."""

    dependency_graph = context.evaluated_depsgraph_get()
    evaluated_object = source_object.evaluated_get(dependency_graph)
    source_mesh = source_object.data
    temporary_mesh = None
    try:
        temporary_mesh = evaluated_object.to_mesh(
            preserve_all_data_layers=True,
            depsgraph=dependency_graph,
        )
        if temporary_mesh is None:
            raise MeshExtractionError("Blender could not create an evaluated mesh.")
        topology = _topology_snapshot(source_mesh, temporary_mesh)
        _triangulate_temporary_mesh(temporary_mesh)
        export_mesh = _extract_mesh_data(
            temporary_mesh,
            evaluated_object.matrix_world,
            scale,
            coordinate_space,
            texture_width,
            texture_height,
            flip_v,
        )
        return export_mesh, topology
    except MeshExtractionError:
        raise
    except Exception as error:
        raise MeshExtractionError(f"Mesh extraction failed: {error}") from error
    finally:
        if temporary_mesh is not None:
            evaluated_object.to_mesh_clear()


def extract_evaluated_mesh(
    context,
    source_object,
    scale: float,
    coordinate_space: str,
    texture_width: int,
    texture_height: int,
    flip_v: bool,
) -> ExportMesh:
    """Extract data from an evaluated mesh and discard diagnostic topology."""

    export_mesh, _topology = extract_evaluated_mesh_with_topology(
        context,
        source_object,
        scale,
        coordinate_space,
        texture_width,
        texture_height,
        flip_v,
    )
    return export_mesh


def extract_evaluated_vertex_frame(
    context,
    source_object,
    scale: float,
    coordinate_space: str,
) -> tuple[tuple[ExportVertex, ...], MeshTopologySnapshot]:
    """Extract one deformed vertex frame without triangulating or reading UVs."""

    dependency_graph = context.evaluated_depsgraph_get()
    evaluated_object = source_object.evaluated_get(dependency_graph)
    source_mesh = source_object.data
    temporary_mesh = None
    try:
        temporary_mesh = evaluated_object.to_mesh(
            preserve_all_data_layers=False,
            depsgraph=dependency_graph,
        )
        if temporary_mesh is None:
            raise MeshExtractionError("Blender could not create an evaluated mesh.")
        topology = _topology_snapshot(source_mesh, temporary_mesh)
        vertices = _extract_vertex_positions(
            temporary_mesh,
            evaluated_object.matrix_world,
            scale,
            coordinate_space,
        )
        return vertices, topology
    except MeshExtractionError:
        raise
    except Exception as error:
        raise MeshExtractionError(f"Mesh extraction failed: {error}") from error
    finally:
        if temporary_mesh is not None:
            evaluated_object.to_mesh_clear()
