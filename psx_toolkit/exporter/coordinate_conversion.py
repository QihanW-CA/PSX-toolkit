"""Pure conversion from Blender coordinates to PS1 integer coordinates."""

from collections.abc import Sequence

from .model import ExportVertex

INT16_MIN = -32768
INT16_MAX = 32767

# Each entry is (Blender source-axis index, sign) for PS1 X, Y, and Z.
PS1_AXIS_MAPPING = (
    (0, 1),
    (2, -1),
    (1, 1),
)


class CoordinateOverflowError(ValueError):
    """Raised when a converted vertex cannot fit in an SVECTOR component."""


def position_for_coordinate_space(local_position, matrix_world, coordinate_space: str):
    """Return a copied local position or its world-space transformation."""

    if coordinate_space == "LOCAL":
        return local_position.copy()
    if coordinate_space == "WORLD":
        return matrix_world @ local_position
    raise ValueError(f"Unsupported coordinate space: {coordinate_space}")


def convert_position(
    position: Sequence[float],
    scale: float,
    *,
    vertex_index: int,
) -> ExportVertex:
    """Scale, round, remap axes, and validate one Blender-space position."""

    if scale <= 0:
        raise ValueError("Export scale must be greater than zero.")

    blender_coordinates = tuple(position)
    remapped_coordinates = tuple(
        blender_coordinates[source_axis] * sign
        for source_axis, sign in PS1_AXIS_MAPPING
    )
    converted = ExportVertex(
        x=round(remapped_coordinates[0] * scale),
        y=round(remapped_coordinates[1] * scale),
        z=round(remapped_coordinates[2] * scale),
    )
    coordinates = (converted.x, converted.y, converted.z)
    if any(value < INT16_MIN or value > INT16_MAX for value in coordinates):
        raise CoordinateOverflowError(
            f"Vertex {vertex_index} converts to {coordinates}, which exceeds "
            "the int16_t range -32768 to 32767."
        )
    return converted
