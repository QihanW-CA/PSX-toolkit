"""Scene-level settings for PSX Toolkit model output."""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)


def _get_animation_start_frame(settings) -> int:
    stored_value = settings.get("animation_start_frame")
    if stored_value is not None:
        return int(stored_value)
    return int(settings.id_data.frame_start)


def _set_animation_start_frame(settings, value: int) -> None:
    settings["animation_start_frame"] = value


def _get_animation_end_frame(settings) -> int:
    stored_value = settings.get("animation_end_frame")
    if stored_value is not None:
        return int(stored_value)
    return int(settings.id_data.frame_end)


def _set_animation_end_frame(settings, value: int) -> None:
    settings["animation_end_frame"] = value


class PSXTOOLKIT_PG_export_settings(bpy.types.PropertyGroup):
    """Store model output choices with the current Blender scene."""

    output_directory: StringProperty(
        name="Output Folder",
        description="Directory where PSX Toolkit writes generated model files",
        default="",
        subtype="DIR_PATH",
    )
    output_filename: StringProperty(
        name="File Name",
        description="Base name for generated C and header files",
        default="psx_model",
    )
    export_scale: FloatProperty(
        name="Export Scale",
        description="PS1 coordinate units per Blender unit",
        default=256.0,
        min=0.000001,
    )
    coordinate_space: EnumProperty(
        name="Coordinate Space",
        description="Choose whether object transforms are included in vertex data",
        items=(
            (
                "LOCAL",
                "Local Space",
                "Export relative to the object's origin without object transforms",
            ),
            (
                "WORLD",
                "World Space",
                "Apply the object's world location, rotation, and scale",
            ),
        ),
        default="LOCAL",
    )
    texture_size_source: EnumProperty(
        name="Source",
        description="Choose how texture dimensions are supplied",
        items=(
            ("MATERIAL", "Material Texture", "Use the selected Blender image size"),
            ("MANUAL", "Manual Size", "Enter texture dimensions manually"),
        ),
        default="MATERIAL",
    )
    texture_image: PointerProperty(
        name="Texture",
        description="Image used only to determine UV dimensions",
        type=bpy.types.Image,
    )
    texture_width: IntProperty(
        name="Width",
        default=256,
        min=1,
        max=256,
    )
    texture_height: IntProperty(
        name="Height",
        default=256,
        min=1,
        max=256,
    )
    flip_v: BoolProperty(
        name="Flip V",
        default=True,
    )
    prepared_mesh: PointerProperty(
        name="Prepared Mesh",
        description="Mesh datablock most recently approved for static export",
        type=bpy.types.Mesh,
        options={"HIDDEN"},
    )
    prepared_topology_fingerprint: StringProperty(
        name="Prepared Topology Fingerprint",
        description="Connectivity fingerprint recorded during preparation",
        default="",
        options={"HIDDEN"},
    )
    animation_name: StringProperty(
        name="Animation Name",
        default="animation",
    )
    animation_start_frame: IntProperty(
        name="Start Frame",
        get=_get_animation_start_frame,
        set=_set_animation_start_frame,
    )
    animation_end_frame: IntProperty(
        name="End Frame",
        get=_get_animation_end_frame,
        set=_set_animation_end_frame,
    )
    animation_frame_step: IntProperty(
        name="Frame Step",
        default=1,
        min=1,
    )
