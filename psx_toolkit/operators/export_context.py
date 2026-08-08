"""Resolve settings shared by static and animation export operators."""

import os
from dataclasses import dataclass
from pathlib import Path

import bpy

from ..exporter.texture_size import TextureSizeError, resolve_texture_size


@dataclass(frozen=True)
class ResolvedExportEnvironment:
    directory: Path
    scale: float
    coordinate_space: str
    texture_width: int
    texture_height: int
    flip_v: bool


def resolve_export_environment(
    operator,
    context: bpy.types.Context,
) -> ResolvedExportEnvironment | None:
    """Validate shared scene settings and report failures to Blender."""

    settings = context.scene.psx_toolkit_export_settings
    directory_value = settings.output_directory.strip()
    if not directory_value:
        operator.report({"ERROR"}, "Select an output folder before exporting.")
        return None

    try:
        directory = Path(bpy.path.abspath(directory_value)).expanduser()
        directory_exists = directory.exists()
        directory_is_valid = directory.is_dir()
    except (OSError, ValueError) as error:
        operator.report({"ERROR"}, f"Invalid output directory: {error}")
        return None
    if not directory_exists:
        operator.report({"ERROR"}, f"Output directory does not exist: {directory}")
        return None
    if not directory_is_valid:
        operator.report({"ERROR"}, f"Output path is not a directory: {directory}")
        return None
    if not os.access(directory, os.W_OK):
        operator.report({"ERROR"}, "Insufficient permission to write export files.")
        return None

    scale = settings.export_scale
    if scale <= 0:
        operator.report({"ERROR"}, "Export scale must be greater than zero.")
        return None
    try:
        texture_width, texture_height = resolve_texture_size(settings)
    except TextureSizeError as error:
        operator.report({"ERROR"}, str(error))
        return None

    return ResolvedExportEnvironment(
        directory=directory,
        scale=scale,
        coordinate_space=settings.coordinate_space,
        texture_width=texture_width,
        texture_height=texture_height,
        flip_v=settings.flip_v,
    )
