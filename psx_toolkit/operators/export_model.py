"""Blender workflow for static PS1 model exports."""

import os
from dataclasses import dataclass
from pathlib import Path

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty

from ..exporter.c_writer import write_model_files
from ..exporter.mesh_extractor import MeshExtractionError, extract_evaluated_mesh
from ..exporter.texture_size import TextureSizeError, resolve_texture_size
from ..utils.mesh_validation import is_mesh_fully_triangulated
from ..utils.naming import sanitize_c_identifier
from .mesh_checks import (
    NON_TRIANGLE_MESSAGE,
    selected_mesh_object_or_report,
    temporary_triangulation_succeeds,
)


@dataclass(frozen=True)
class _ResolvedExportSettings:
    directory: Path
    symbol_base: str
    scale: float
    coordinate_space: str
    texture_width: int
    texture_height: int
    flip_v: bool


def _write_and_report(
    operator,
    directory: Path,
    symbol_base: str,
    mesh,
    *,
    overwrite: bool,
):
    """Write both model files and translate file errors into Blender reports."""

    try:
        source_path, header_path = write_model_files(
            directory,
            symbol_base,
            mesh,
            overwrite=overwrite,
        )
    except FileExistsError:
        operator.report({"ERROR"}, "One or both output files already exist.")
        return {"CANCELLED"}
    except FileNotFoundError as error:
        operator.report({"ERROR"}, str(error))
        return {"CANCELLED"}
    except NotADirectoryError as error:
        operator.report({"ERROR"}, str(error))
        return {"CANCELLED"}
    except PermissionError:
        operator.report({"ERROR"}, "Insufficient permission to write export files.")
        return {"CANCELLED"}
    except OSError as error:
        operator.report({"ERROR"}, f"Failed to create export files: {error}")
        return {"CANCELLED"}

    operator.report(
        {"INFO"},
        f"Exported {source_path.name} and {header_path.name} successfully.",
    )
    return {"FINISHED"}


def _extract_or_report(
    operator,
    context,
    source_object,
    scale: float,
    coordinate_space: str,
    texture_width: int,
    texture_height: int,
    flip_v: bool,
):
    """Extract evaluated mesh data and report validation failures in Blender."""

    try:
        return extract_evaluated_mesh(
            context,
            source_object,
            scale,
            coordinate_space,
            texture_width,
            texture_height,
            flip_v,
        )
    except MeshExtractionError as error:
        operator.report({"ERROR"}, str(error))
        return None
    except Exception as error:
        operator.report({"ERROR"}, f"Mesh extraction failed: {error}")
        return None


class PSXTOOLKIT_OT_confirm_overwrite(bpy.types.Operator):
    """Confirm replacement of both generated model files."""

    bl_idname = "psx_toolkit.confirm_overwrite"
    bl_label = "Overwrite PS1 Model Files"
    bl_options = {"INTERNAL"}

    directory: StringProperty(options={"HIDDEN", "SKIP_SAVE"})
    symbol_base: StringProperty(options={"HIDDEN", "SKIP_SAVE"})
    export_scale: FloatProperty(options={"HIDDEN", "SKIP_SAVE"})
    coordinate_space: StringProperty(options={"HIDDEN", "SKIP_SAVE"})
    texture_width: IntProperty(options={"HIDDEN", "SKIP_SAVE"})
    texture_height: IntProperty(options={"HIDDEN", "SKIP_SAVE"})
    flip_v: BoolProperty(options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        """Ask for explicit permission before replacing either file."""

        return context.window_manager.invoke_confirm(
            self,
            event,
            title="Existing Export Files",
            message=(
                f"{self.symbol_base}.c or {self.symbol_base}.h already exists. "
                "Overwrite both files?"
            ),
            confirm_text="Overwrite Both",
            icon="QUESTION",
        )

    def execute(self, context: bpy.types.Context):
        """Write both files after overwrite permission is granted."""

        source_object = selected_mesh_object_or_report(self, context)
        if source_object is None:
            return {"CANCELLED"}
        mesh = _extract_or_report(
            self,
            context,
            source_object,
            self.export_scale,
            self.coordinate_space,
            self.texture_width,
            self.texture_height,
            self.flip_v,
        )
        if mesh is None:
            return {"CANCELLED"}

        return _write_and_report(
            self,
            Path(self.directory),
            self.symbol_base,
            mesh,
            overwrite=True,
        )

    def cancel(self, context: bpy.types.Context) -> None:
        """Report that the user kept the existing files."""

        self.report({"INFO"}, "Export cancelled. Existing files were not changed.")


class PSXTOOLKIT_OT_export_model(bpy.types.Operator):
    """Validate a mesh and export static C model data."""

    bl_idname = "psx_toolkit.export_model"
    bl_label = "Export PS1 Model"
    bl_description = "Export static PS1 mesh data to C and header files"
    bl_options = {"REGISTER"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        """Validate settings and request temporary triangulation when needed."""

        source_object = selected_mesh_object_or_report(self, context)
        if source_object is None:
            return {"CANCELLED"}
        if self._resolve_output(context) is None:
            return {"CANCELLED"}
        if is_mesh_fully_triangulated(source_object.data):
            return self.execute(context)

        return context.window_manager.invoke_confirm(
            self,
            event,
            title="Temporary Triangulation",
            message=NON_TRIANGLE_MESSAGE,
            confirm_text="Continue",
            icon="QUESTION",
        )

    def _validate_temporary_triangulation(self, mesh) -> bool:
        try:
            triangulation_succeeded = temporary_triangulation_succeeds(mesh)
        except Exception as error:
            self.report({"ERROR"}, f"Temporary triangulation failed: {error}")
            return False

        if not triangulation_succeeded:
            self.report(
                {"ERROR"},
                "Temporary triangulation produced non-triangle faces.",
            )
            return False
        return True

    def _resolve_output(
        self,
        context: bpy.types.Context,
    ) -> _ResolvedExportSettings | None:
        settings = context.scene.psx_toolkit_export_settings
        directory_value = settings.output_directory.strip()
        if not directory_value:
            self.report({"ERROR"}, "Select an output folder before exporting.")
            return None

        try:
            directory = Path(bpy.path.abspath(directory_value)).expanduser()
            directory_exists = directory.exists()
            directory_is_valid = directory.is_dir()
        except (OSError, ValueError) as error:
            self.report({"ERROR"}, f"Invalid output directory: {error}")
            return None
        if not directory_exists:
            self.report({"ERROR"}, f"Output directory does not exist: {directory}")
            return None
        if not directory_is_valid:
            self.report({"ERROR"}, f"Output path is not a directory: {directory}")
            return None
        if not os.access(directory, os.W_OK):
            self.report({"ERROR"}, "Insufficient permission to write export files.")
            return None

        filename = settings.output_filename.strip()
        if not filename:
            self.report({"ERROR"}, "Enter an output filename before exporting.")
            return None

        symbol_base = sanitize_c_identifier(filename)
        settings.output_filename = symbol_base
        scale = settings.export_scale
        if scale <= 0:
            self.report({"ERROR"}, "Export scale must be greater than zero.")
            return None
        try:
            texture_width, texture_height = resolve_texture_size(settings)
        except TextureSizeError as error:
            self.report({"ERROR"}, str(error))
            return None

        return _ResolvedExportSettings(
            directory=directory,
            symbol_base=symbol_base,
            scale=scale,
            coordinate_space=settings.coordinate_space,
            texture_width=texture_width,
            texture_height=texture_height,
            flip_v=settings.flip_v,
        )

    def execute(self, context: bpy.types.Context):
        """Finish validation, then select or write the output files."""

        source_object = selected_mesh_object_or_report(self, context)
        if source_object is None:
            return {"CANCELLED"}

        if not is_mesh_fully_triangulated(source_object.data):
            if not self._validate_temporary_triangulation(source_object.data):
                return {"CANCELLED"}

        resolved_output = self._resolve_output(context)
        if resolved_output is None:
            return {"CANCELLED"}
        mesh = _extract_or_report(
            self,
            context,
            source_object,
            resolved_output.scale,
            resolved_output.coordinate_space,
            resolved_output.texture_width,
            resolved_output.texture_height,
            resolved_output.flip_v,
        )
        if mesh is None:
            return {"CANCELLED"}

        source_path = resolved_output.directory / f"{resolved_output.symbol_base}.c"
        header_path = resolved_output.directory / f"{resolved_output.symbol_base}.h"

        if source_path.exists() or header_path.exists():
            bpy.ops.psx_toolkit.confirm_overwrite(
                "INVOKE_DEFAULT",
                directory=str(resolved_output.directory),
                symbol_base=resolved_output.symbol_base,
                export_scale=resolved_output.scale,
                coordinate_space=resolved_output.coordinate_space,
                texture_width=resolved_output.texture_width,
                texture_height=resolved_output.texture_height,
                flip_v=resolved_output.flip_v,
            )
            return {"FINISHED"}

        return _write_and_report(
            self,
            resolved_output.directory,
            resolved_output.symbol_base,
            mesh,
            overwrite=False,
        )

    def cancel(self, context: bpy.types.Context) -> None:
        """Report cancellation of temporary triangulation and export."""

        self.report({"INFO"}, "Export cancelled.")
