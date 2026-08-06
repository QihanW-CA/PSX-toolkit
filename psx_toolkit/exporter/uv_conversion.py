"""Pure conversion and deduplication of Blender loop UV coordinates."""

from collections.abc import Iterable

from .model import ExportUV
from .texture_size import validate_texture_size


def _clamp(value: int, maximum: int) -> int:
    return max(0, min(maximum, value))


def convert_uv(
    u: float,
    v: float,
    width: int,
    height: int,
    *,
    flip_v: bool,
) -> ExportUV:
    """Convert a normalized Blender UV to pixel coordinates."""

    width, height = validate_texture_size(width, height)
    maximum_u = width - 1
    maximum_v = height - 1
    converted_v = 1.0 - v if flip_v else v
    return ExportUV(
        u=_clamp(round(u * maximum_u), maximum_u),
        v=_clamp(round(converted_v * maximum_v), maximum_v),
    )


def deduplicate_uvs(
    coordinates: Iterable[ExportUV],
) -> tuple[tuple[ExportUV, ...], tuple[int, ...]]:
    """Return unique UVs and an index for every input corner."""

    unique_uvs: list[ExportUV] = []
    indices: list[int] = []
    lookup: dict[ExportUV, int] = {}

    for coordinate in coordinates:
        index = lookup.get(coordinate)
        if index is None:
            index = len(unique_uvs)
            lookup[coordinate] = index
            unique_uvs.append(coordinate)
        indices.append(index)

    return tuple(unique_uvs), tuple(indices)
