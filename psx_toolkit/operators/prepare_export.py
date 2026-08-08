"""Validate a mesh and prove that temporary triangulation is safe."""

import bpy

from ..utils.mesh_validation import (
    is_mesh_fully_triangulated,
    mark_mesh_prepared,
)
from .mesh_checks import (
    NON_TRIANGLE_MESSAGE,
    selected_mesh_or_report,
    temporary_triangulation_succeeds,
)


class PSXTOOLKIT_OT_prepare_export(bpy.types.Operator):
    """Validate the selected mesh before a future PS1 export."""

    bl_idname = "psx_toolkit.prepare_export"
    bl_label = "Prepare PSX Export"
    bl_description = "Validate the selected mesh for PS1 export"
    bl_options = {"REGISTER"}

    def _record_prepared_state(self, context, mesh) -> None:
        settings = context.scene.psx_toolkit_export_settings
        mark_mesh_prepared(settings, mesh)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        """Validate selection and request confirmation only when needed."""

        mesh = selected_mesh_or_report(self, context)
        if mesh is None:
            return {"CANCELLED"}
        if is_mesh_fully_triangulated(mesh):
            self._record_prepared_state(context, mesh)
            self.report({"INFO"}, "Mesh prepared for PSX export.")
            return {"FINISHED"}

        return context.window_manager.invoke_confirm(
            self,
            event,
            title="Temporary Triangulation",
            message=NON_TRIANGLE_MESSAGE,
            confirm_text="Continue",
            icon="QUESTION",
        )

    def execute(self, context: bpy.types.Context):
        """Perform and immediately discard temporary triangulation."""

        mesh = selected_mesh_or_report(self, context)
        if mesh is None:
            return {"CANCELLED"}
        if is_mesh_fully_triangulated(mesh):
            self._record_prepared_state(context, mesh)
            self.report({"INFO"}, "Mesh prepared for PSX export.")
            return {"FINISHED"}

        try:
            triangulation_succeeded = temporary_triangulation_succeeds(mesh)
        except Exception as error:
            self.report({"ERROR"}, f"Temporary triangulation failed: {error}")
            return {"CANCELLED"}

        if not triangulation_succeeded:
            self.report(
                {"ERROR"},
                "Temporary triangulation produced non-triangle faces.",
            )
            return {"CANCELLED"}

        self._record_prepared_state(context, mesh)
        self.report(
            {"INFO"},
            "Mesh prepared for PSX export. The original mesh was not modified.",
        )
        return {"FINISHED"}
