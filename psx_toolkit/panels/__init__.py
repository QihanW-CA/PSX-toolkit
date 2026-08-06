"""Blender UI panels provided by PSX Toolkit."""

import bpy

from .main_panel import PSXTOOLKIT_PT_main_panel

_classes = (PSXTOOLKIT_PT_main_panel,)


def register() -> None:
    """Register PSX Toolkit panels."""

    for panel_class in _classes:
        bpy.utils.register_class(panel_class)


def unregister() -> None:
    """Unregister PSX Toolkit panels."""

    for panel_class in reversed(_classes):
        bpy.utils.unregister_class(panel_class)
