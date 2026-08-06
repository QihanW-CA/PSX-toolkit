"""Blender operators provided by PSX Toolkit."""

import bpy

from .export_model import (
    PSXTOOLKIT_OT_confirm_overwrite,
    PSXTOOLKIT_OT_export_model,
)
from .prepare_export import PSXTOOLKIT_OT_prepare_export

_classes = (
    PSXTOOLKIT_OT_prepare_export,
    PSXTOOLKIT_OT_confirm_overwrite,
    PSXTOOLKIT_OT_export_model,
)


def register() -> None:
    """Register PSX Toolkit operators."""

    for operator_class in _classes:
        bpy.utils.register_class(operator_class)


def unregister() -> None:
    """Unregister PSX Toolkit operators."""

    for operator_class in reversed(_classes):
        bpy.utils.unregister_class(operator_class)
