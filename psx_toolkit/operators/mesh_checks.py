"""Shared Blender-specific mesh selection and triangulation helpers."""

import bmesh
import bpy

NON_TRIANGLE_MESSAGE = (
    "The selected mesh contains non-triangle faces. It can be triangulated "
    "temporarily during export without modifying the original mesh."
)


def selected_mesh_object_or_report(operator, context: bpy.types.Context):
    """Return the one selected mesh object, reporting validation failures."""

    selected_objects = context.selected_objects
    if not selected_objects:
        operator.report({"ERROR"}, "No object is selected. Select one mesh object.")
        return None
    if len(selected_objects) > 1:
        operator.report(
            {"ERROR"},
            "More than one object is selected. Select one mesh object.",
        )
        return None

    selected_object = selected_objects[0]
    if selected_object.type != "MESH":
        operator.report({"ERROR"}, "The selected object is not a mesh.")
        return None
    return selected_object


def selected_mesh_or_report(operator, context: bpy.types.Context):
    """Return the one selected mesh datablock, reporting validation failures."""

    selected_object = selected_mesh_object_or_report(operator, context)
    return selected_object.data if selected_object is not None else None


def temporary_triangulation_succeeds(mesh: bpy.types.Mesh) -> bool:
    """Triangulate a temporary BMesh, verify it, and always release it."""

    temporary_mesh = bmesh.new()
    try:
        temporary_mesh.from_mesh(mesh)
        bmesh.ops.triangulate(temporary_mesh, faces=list(temporary_mesh.faces))
        return all(len(face.verts) == 3 for face in temporary_mesh.faces)
    finally:
        temporary_mesh.free()
