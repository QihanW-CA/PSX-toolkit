"""Pure data structures and helpers for baked vertex animation."""

from dataclasses import dataclass

from ..utils.naming import sanitize_c_identifier
from .model import ExportTriangle, ExportUV, ExportVertex
from .topology_diagnostics import MeshTopologySnapshot


class AnimationTopologyError(ValueError):
    """Raised when a sampled frame differs from reference topology."""


@dataclass(frozen=True)
class BakedMeshAnimation:
    """One mesh's fixed topology and baked vertices at synchronized frames."""

    mesh_name: str
    source_frames: tuple[int, ...]
    vertex_frames: tuple[tuple[ExportVertex, ...], ...]
    uvs: tuple[ExportUV, ...]
    triangles: tuple[ExportTriangle, ...]

    def __post_init__(self) -> None:
        """Require every baked frame to preserve one fixed vertex count."""

        if not self.vertex_frames:
            return
        vertex_count = len(self.vertex_frames[0])
        if any(len(frame) != vertex_count for frame in self.vertex_frames):
            raise ValueError(
                "Every animation frame must contain the reference vertex count."
            )

    @property
    def frame_count(self) -> int:
        return len(self.vertex_frames)

    @property
    def vertex_count(self) -> int:
        return len(self.vertex_frames[0]) if self.vertex_frames else 0


def sampled_frame_range(start: int, end: int, step: int) -> tuple[int, ...]:
    """Return an inclusive-start/end range, stopping before an unhit end."""

    if start > end:
        raise ValueError("Animation start frame cannot be greater than end frame.")
    if step < 1:
        raise ValueError("Animation frame step must be at least 1.")
    frames = tuple(range(start, end + 1, step))
    if not frames:
        raise ValueError("The animation frame range produced no sampled frames.")
    return frames


def resolve_animation_output_bases(
    mesh_names: tuple[str, ...],
    animation_name: str,
) -> tuple[str, ...]:
    """Resolve unique C-safe file and symbol bases for animated meshes."""

    mesh_identifiers = tuple(
        sanitize_c_identifier(mesh_name) for mesh_name in mesh_names
    )
    explicit_name = animation_name.strip()
    if explicit_name:
        root = sanitize_c_identifier(explicit_name)
        if len(mesh_identifiers) == 1:
            bases = (root,)
        else:
            bases = tuple(f"{root}_{mesh}" for mesh in mesh_identifiers)
    else:
        bases = tuple(f"{mesh}_animation" for mesh in mesh_identifiers)

    if len(bases) != len(set(bases)):
        raise ValueError(
            "Selected mesh names collide after C identifier sanitization."
        )
    return bases


def flatten_vertex_frames(
    vertex_frames: tuple[tuple[ExportVertex, ...], ...],
) -> tuple[ExportVertex, ...]:
    """Flatten frames in frame-major order for contiguous C storage."""

    return tuple(vertex for frame in vertex_frames for vertex in frame)


def validate_animation_topology(
    mesh_name: str,
    frame: int,
    reference: MeshTopologySnapshot,
    sampled: MeshTopologySnapshot,
) -> None:
    """Require stable indexed pre-triangulation topology between frames.

    Matching connectivity under the same numeric vertex indices is the exporter's
    guarantee that index N continues to identify the same deforming vertex. This
    version deliberately rejects mismatches instead of attempting index remapping.
    """

    if sampled.source_vertex_count != reference.source_vertex_count:
        raise AnimationTopologyError(
            f"Mesh '{mesh_name}' changes source vertex count at frame {frame}."
        )
    if len(sampled.source_polygons) != len(reference.source_polygons):
        raise AnimationTopologyError(
            f"Mesh '{mesh_name}' changes source polygon count at frame {frame}."
        )
    if sampled.source_polygon_topology != reference.source_polygon_topology:
        raise AnimationTopologyError(
            f"Mesh '{mesh_name}' changes source polygon topology at frame {frame}."
        )
    if sampled.evaluated_vertex_count != reference.evaluated_vertex_count:
        raise AnimationTopologyError(
            f"Mesh '{mesh_name}' changes vertex count at frame {frame}."
        )
    if len(sampled.evaluated_polygons) != len(reference.evaluated_polygons):
        raise AnimationTopologyError(
            f"Mesh '{mesh_name}' changes polygon count at frame {frame}."
        )
    if not reference.has_stable_index_sequence or not sampled.has_stable_index_sequence:
        raise AnimationTopologyError(
            f"Mesh '{mesh_name}' cannot preserve stable vertex indices at frame "
            f"{frame}."
        )
    if sampled.evaluated_polygon_topology != reference.evaluated_polygon_topology:
        raise AnimationTopologyError(
            f"Mesh '{mesh_name}' changes polygon topology at frame {frame}. "
            "Baked vertex animation requires fixed topology."
        )
