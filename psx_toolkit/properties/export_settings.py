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
