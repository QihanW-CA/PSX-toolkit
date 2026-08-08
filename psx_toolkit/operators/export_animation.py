"""Blender operators for baked multi-mesh vertex animation export."""

from dataclasses import dataclass
from pathlib import Path

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty

from ..exporter.animation_extractor import (
    AnimationExtractionError,
    extract_baked_animations,
)
from ..exporter.animation_model import (
    resolve_animation_output_bases,
    sampled_frame_range,
)
from ..exporter.c_animation_writer import (
    animation_output_paths,
    write_animation_files,
)
from ..utils.naming import sanitize_c_identifier
from .export_context import ResolvedExportEnvironment, resolve_export_environment


@dataclass(frozen=True)
class _AnimationRequest:
    source_objects: tuple
    animation_name: str
    frames: tuple[int, ...]
    environment: ResolvedExportEnvironment


def _selected_mesh_objects(context: bpy.types.Context) -> tuple:
    return tuple(
        sorted(
            (
                selected_object
                for selected_object in context.selected_objects
                if selected_object.type == "MESH"
            ),
            key=lambda selected_object: selected_object.name,
        )
    )


def _validate_symbol_names(operator, source_objects, animation_name: str) -> bool:
    try:
        resolve_animation_output_bases(
            tuple(source_object.name for source_object in source_objects),
            animation_name,
        )
    except ValueError as error:
        operator.report(
            {"ERROR"},
            str(error),
        )
        return False
    return True


def _resolve_animation_request(
    operator,
    context: bpy.types.Context,
) -> _AnimationRequest | None:
    source_objects = _selected_mesh_objects(context)
    if not source_objects:
        operator.report({"ERROR"}, "No mesh objects are selected.")
        return None

    settings = context.scene.psx_toolkit_export_settings
    animation_name = settings.animation_name.strip()
    if animation_name:
        animation_name = sanitize_c_identifier(animation_name)
    settings.animation_name = animation_name

    try:
        frames = sampled_frame_range(
            settings.animation_start_frame,
            settings.animation_end_frame,
            settings.animation_frame_step,
        )
    except ValueError as error:
        operator.report({"ERROR"}, str(error))
        return None

    if not _validate_symbol_names(operator, source_objects, animation_name):
        return None
    environment = resolve_export_environment(operator, context)
    if environment is None:
        return None
    return _AnimationRequest(
        source_objects=source_objects,
        animation_name=animation_name,
        frames=frames,
        environment=environment,
    )


def _extract_or_report(operator, context, request: _AnimationRequest):
    try:
        return extract_baked_animations(
            context,
            request.source_objects,
            request.frames,
            scale=request.environment.scale,
            coordinate_space=request.environment.coordinate_space,
            texture_width=request.environment.texture_width,
            texture_height=request.environment.texture_height,
            flip_v=request.environment.flip_v,
        )
    except AnimationExtractionError as error:
        operator.report({"ERROR"}, str(error))
        return None
    except Exception as error:
        operator.report({"ERROR"}, f"Animation extraction failed: {error}")
        return None


def _write_and_report(
    operator,
    directory: Path,
    animations,
    animation_name: str,
    *,
    overwrite: bool,
):
    try:
        paths = write_animation_files(
            directory,
            animations,
            animation_name,
            overwrite=overwrite,
        )
    except FileExistsError:
        operator.report({"ERROR"}, "One or more animation files already exist.")
        return {"CANCELLED"}
    except FileNotFoundError as error:
        operator.report({"ERROR"}, str(error))
        return {"CANCELLED"}
    except NotADirectoryError as error:
        operator.report({"ERROR"}, str(error))
        return {"CANCELLED"}
    except PermissionError:
        operator.report({"ERROR"}, "Insufficient permission to write animation files.")
        return {"CANCELLED"}
    except (OSError, ValueError) as error:
        operator.report({"ERROR"}, f"Failed to create animation files: {error}")
        return {"CANCELLED"}

    operator.report(
        {"INFO"},
        f"Exported {len(paths) // 2} animated mesh file pairs successfully.",
    )
    return {"FINISHED"}


class PSXTOOLKIT_OT_confirm_animation_overwrite(bpy.types.Operator):
    """Confirm replacement of all selected meshes' animation files."""

    bl_idname = "psx_toolkit.confirm_animation_overwrite"
    bl_label = "Overwrite Animation Files"
    bl_options = {"INTERNAL"}

    directory: StringProperty(options={"HIDDEN", "SKIP_SAVE"})
    animation_name: StringProperty(options={"HIDDEN", "SKIP_SAVE"})
    start_frame: IntProperty(options={"HIDDEN", "SKIP_SAVE"})
    end_frame: IntProperty(options={"HIDDEN", "SKIP_SAVE"})
    frame_step: IntProperty(options={"HIDDEN", "SKIP_SAVE"})
    export_scale: FloatProperty(options={"HIDDEN", "SKIP_SAVE"})
    coordinate_space: StringProperty(options={"HIDDEN", "SKIP_SAVE"})
    texture_width: IntProperty(options={"HIDDEN", "SKIP_SAVE"})
    texture_height: IntProperty(options={"HIDDEN", "SKIP_SAVE"})
    flip_v: BoolProperty(options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        """Ask permission before replacing any animation output."""

        return context.window_manager.invoke_confirm(
            self,
            event,
            title="Existing Animation Files",
            message="Animation output files already exist. Overwrite all of them?",
            confirm_text="Overwrite All",
            icon="QUESTION",
        )

    def execute(self, context: bpy.types.Context):
        """Resample and replace every animation file after confirmation."""

        source_objects = _selected_mesh_objects(context)
        if not source_objects:
            self.report({"ERROR"}, "No mesh objects are selected.")
            return {"CANCELLED"}
        if not _validate_symbol_names(self, source_objects, self.animation_name):
            return {"CANCELLED"}
        try:
            frames = sampled_frame_range(
                self.start_frame,
                self.end_frame,
                self.frame_step,
            )
        except ValueError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        request = _AnimationRequest(
            source_objects=source_objects,
            animation_name=self.animation_name,
            frames=frames,
            environment=ResolvedExportEnvironment(
                directory=Path(self.directory),
                scale=self.export_scale,
                coordinate_space=self.coordinate_space,
                texture_width=self.texture_width,
                texture_height=self.texture_height,
                flip_v=self.flip_v,
            ),
        )
        animations = _extract_or_report(self, context, request)
        if animations is None:
            return {"CANCELLED"}
        return _write_and_report(
            self,
            request.environment.directory,
            animations,
            request.animation_name,
            overwrite=True,
        )

    def cancel(self, context: bpy.types.Context) -> None:
        """Report that existing animation files were retained."""

        self.report(
            {"INFO"},
            "Animation export cancelled. Existing files were not changed.",
        )


class PSXTOOLKIT_OT_export_animation(bpy.types.Operator):
    """Export selected evaluated meshes as baked vertex animation."""

    bl_idname = "psx_toolkit.export_animation"
    bl_label = "Export Animation"
    bl_description = "Export selected meshes as baked PS1 vertex animation"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context):
        """Validate, sample, and write synchronized animation files."""

        request = _resolve_animation_request(self, context)
        if request is None:
            return {"CANCELLED"}
        animations = _extract_or_report(self, context, request)
        if animations is None:
            return {"CANCELLED"}

        try:
            paths = animation_output_paths(
                request.environment.directory,
                animations,
                request.animation_name,
            )
        except ValueError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        if any(path.exists() for path in paths):
            bpy.ops.psx_toolkit.confirm_animation_overwrite(
                "INVOKE_DEFAULT",
                directory=str(request.environment.directory),
                animation_name=request.animation_name,
                start_frame=request.frames[0],
                end_frame=request.frames[-1],
                frame_step=(
                    request.frames[1] - request.frames[0]
                    if len(request.frames) > 1
                    else 1
                ),
                export_scale=request.environment.scale,
                coordinate_space=request.environment.coordinate_space,
                texture_width=request.environment.texture_width,
                texture_height=request.environment.texture_height,
                flip_v=request.environment.flip_v,
            )
            return {"FINISHED"}

        return _write_and_report(
            self,
            request.environment.directory,
            animations,
            request.animation_name,
            overwrite=False,
        )
