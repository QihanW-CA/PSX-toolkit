"""Sample evaluated Blender meshes into fixed-topology baked animations."""

from dataclasses import dataclass, field

from .animation_model import (
    AnimationTopologyError,
    BakedMeshAnimation,
    validate_animation_topology,
)
from .mesh_extractor import (
    MeshExtractionError,
    extract_evaluated_vertex_frame,
    extract_evaluated_mesh_with_topology,
)
from .model import ExportMesh, ExportVertex
from .topology_diagnostics import MeshTopologySnapshot

UINT16_MAX = 65535


class AnimationExtractionError(ValueError):
    """Raised when sampled meshes cannot form a fixed-topology animation."""


@dataclass
class _AnimationBuilder:
    mesh_name: str
    reference: ExportMesh | None = None
    reference_topology: MeshTopologySnapshot | None = None
    vertex_frames: list[tuple[ExportVertex, ...]] = field(default_factory=list)


def extract_baked_animations(
    context,
    source_objects,
    frames: tuple[int, ...],
    *,
    scale: float,
    coordinate_space: str,
    texture_width: int,
    texture_height: int,
    flip_v: bool,
) -> tuple[BakedMeshAnimation, ...]:
    """Sample every object at every frame and restore the timeline afterward."""

    if not source_objects:
        raise AnimationExtractionError("No mesh objects are selected.")
    if not frames:
        raise AnimationExtractionError("The animation has no sampled frames.")
    if len(frames) > UINT16_MAX:
        raise AnimationExtractionError(
            "Animation frame count exceeds the uint16_t limit of 65535."
        )

    scene = context.scene
    original_frame = scene.frame_current
    original_subframe = scene.frame_subframe
    builders = [
        _AnimationBuilder(source_object.name) for source_object in source_objects
    ]

    try:
        for frame in frames:
            scene.frame_set(frame)
            for source_object, builder in zip(source_objects, builders, strict=True):
                try:
                    if builder.reference is None:
                        # Static topology and UV data are captured exactly once.
                        sampled, sampled_topology = (
                            extract_evaluated_mesh_with_topology(
                                context,
                                source_object,
                                scale,
                                coordinate_space,
                                texture_width,
                                texture_height,
                                flip_v,
                            )
                        )
                        sampled_vertices = sampled.vertices
                    else:
                        # Later samples intentionally skip UVs and triangulation.
                        sampled_vertices, sampled_topology = (
                            extract_evaluated_vertex_frame(
                                context,
                                source_object,
                                scale,
                                coordinate_space,
                            )
                        )
                except MeshExtractionError as error:
                    raise AnimationExtractionError(
                        f"Mesh '{source_object.name}' at frame {frame}: {error}"
                    ) from error

                if builder.reference is None:
                    builder.reference = sampled
                    builder.reference_topology = sampled_topology
                else:
                    try:
                        if builder.reference_topology is None:
                            raise AnimationExtractionError(
                                f"Mesh '{source_object.name}' has no reference "
                                "topology."
                            )
                        validate_animation_topology(
                            source_object.name,
                            frame,
                            builder.reference_topology,
                            sampled_topology,
                        )
                    except AnimationTopologyError as error:
                        raise AnimationExtractionError(str(error)) from error
                if len(sampled_vertices) != sampled_topology.evaluated_vertex_count:
                    raise AnimationExtractionError(
                        f"Mesh '{source_object.name}' produced an incomplete vertex "
                        f"frame at frame {frame}."
                    )
                builder.vertex_frames.append(sampled_vertices)
    finally:
        scene.frame_set(original_frame, subframe=original_subframe)

    animations = []
    for builder in builders:
        if builder.reference is None:
            raise AnimationExtractionError(
                f"Mesh '{builder.mesh_name}' produced no sampled data."
            )
        animations.append(
            BakedMeshAnimation(
                mesh_name=builder.mesh_name,
                source_frames=frames,
                vertex_frames=tuple(builder.vertex_frames),
                uvs=builder.reference.uvs,
                triangles=builder.reference.triangles,
            )
        )
    return tuple(animations)
