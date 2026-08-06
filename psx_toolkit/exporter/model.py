"""Pure data structures for an exported static PS1 mesh."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportVertex:
    """One transformed vertex in PS1 coordinate space."""

    x: int
    y: int
    z: int


@dataclass(frozen=True)
class ExportUV:
    """One deduplicated 8-bit texture coordinate."""

    u: int
    v: int


@dataclass(frozen=True)
class ExportTriangle:
    """Three vertex indices and their three corner UV indices."""

    vertex: tuple[int, int, int]
    uv: tuple[int, int, int]


@dataclass(frozen=True)
class ExportMesh:
    """Validated static mesh data ready for C formatting."""

    vertices: tuple[ExportVertex, ...]
    uvs: tuple[ExportUV, ...]
    triangles: tuple[ExportTriangle, ...]
