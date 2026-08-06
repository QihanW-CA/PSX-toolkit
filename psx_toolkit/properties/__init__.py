"""Blender properties provided by PSX Toolkit."""

import bpy
from bpy.props import PointerProperty

from .export_settings import PSXTOOLKIT_PG_export_settings


def register() -> None:
    """Register export settings and attach them to Blender scenes."""

    bpy.utils.register_class(PSXTOOLKIT_PG_export_settings)
    bpy.types.Scene.psx_toolkit_export_settings = PointerProperty(
        type=PSXTOOLKIT_PG_export_settings,
    )


def unregister() -> None:
    """Remove scene settings and unregister their property group."""

    del bpy.types.Scene.psx_toolkit_export_settings
    bpy.utils.unregister_class(PSXTOOLKIT_PG_export_settings)
