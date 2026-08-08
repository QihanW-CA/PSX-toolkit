# PSX Toolkit

PSX Toolkit is a Blender add-on for exporting 3D models and baked vertex animations as C data for native PlayStation 1 development.

The current version is designed around **PSn00bSDK**. It exports model and animation data into `.c` and `.h` files that can be added directly to a PS1 project.

> **Status:** Early beta. The core Blender → C → PSn00bSDK pipeline is working and has been verified with textured models and baked vertex animation. The project is ready for experimentation and testing, but the output format and workflow may still change.

## Features

- Export mesh vertices as PS1 `SVECTOR` data
- Export triangle vertex indices
- Export per-corner UV coordinates
- Independent vertex and UV indices
- Temporary non-destructive triangulation during export
- Configurable texture dimensions for UV conversion
- Optional V-axis flipping
- Local-space and world-space export
- Baked vertex animation export
- Configurable animation start frame, end frame, and frame step
- Topology validation for animation export
- Generated `.c` and `.h` files for C projects
- Output intended for PSn00bSDK projects

## Tested Pipeline

PSX Toolkit has been tested through the following complete workflow:

```text
Blender
   ↓
PSX Toolkit
   ↓
Generated C model / animation data
   ↓
PSn00bSDK
   ↓
PlayStation 1 rendering
```

The current pipeline has been verified with:

- exported geometry
- exported triangle indices
- exported UV mapping
- textured `POLY_FT3` rendering
- baked vertex animation
- GTE transformation and projection
- depth-sorted Ordering Table rendering

## Requirements

- Blender 4.2 or newer
- A PlayStation 1 C development environment
- PSn00bSDK is the currently tested target

PSX Toolkit is an **asset exporter**, not a game engine or renderer.

Runtime responsibilities such as texture loading, primitive creation, GTE setup, Ordering Table management, animation playback, and game logic remain part of the PS1 application.

## Installation

1. Download the PSX Toolkit add-on ZIP.
2. Open Blender.
3. Open **Edit → Preferences → Add-ons**.
4. Install the ZIP using Blender's add-on installation interface.
5. Enable **PSX Toolkit**.
6. In the 3D Viewport, open the sidebar and select the **PSX Toolkit** tab.

## Model Export

A typical model export workflow is:

1. Prepare a Blender Mesh.
2. Create and verify its UV map if the model will use a texture.
3. Select the Mesh.
4. Click **Prepare PSX Export**.
5. Configure the **Model Output** settings.
6. Configure the intended texture dimensions.
7. Choose Local Space or World Space as appropriate.
8. Export the model.
9. Add the generated `.c` and `.h` files to your PS1 project.

The exporter triangulates the evaluated mesh temporarily during export. The source mesh does not need to be destructively triangulated beforehand.

## UV Export

Blender UV coordinates are stored per face corner rather than directly per mesh vertex. PSX Toolkit preserves this relationship.

This means:

- UV seams are supported.
- One model vertex may use different UV coordinates on different faces.
- Triangle vertex indices and triangle UV indices are independent.
- UV coordinates are exported from the same triangulated mesh used to generate triangle data.

Conceptually, each triangle contains:

```c
typedef struct {
    uint16_t vertex[3];
    uint16_t uv[3];
} PSXTriangle;
```

and UV coordinates are stored separately:

```c
typedef struct {
    uint8_t u;
    uint8_t v;
} PSXUV;
```

At runtime, vertex and UV indices should be resolved independently:

```c
v0  = vertices[triangle.vertex[0]];
v1  = vertices[triangle.vertex[1]];
v2  = vertices[triangle.vertex[2]];

uv0 = uvs[triangle.uv[0]];
uv1 = uvs[triangle.uv[1]];
uv2 = uvs[triangle.uv[2]];
```

Do not assume that a vertex index is also a UV index.

### Texture Dimensions

Blender UV coordinates are normalized, while PS1 texture coordinates are integer texel coordinates.

PSX Toolkit converts UVs using the configured texture dimensions.

**Material Texture** mode uses the dimensions of the image explicitly selected
in the panel. **Manual Size** mode uses the entered width and height. The add-on
does not automatically select an image from material nodes.

Make sure the texture dimensions used during export match the texture layout expected by the PS1 application.

The exporter can also flip the V axis to match the expected PS1 texture orientation.

## Animation Export

PSX Toolkit currently uses **baked vertex animation**.

A typical workflow is:

1. Rig and animate the model normally in Blender.
2. Select the animated Mesh.
3. Configure **Start Frame**.
4. Configure **End Frame**.
5. Configure **Frame Step**.
6. Click **Export Animation**.
7. Add the generated animation `.c` and `.h` files to the PS1 project.

For each sampled Blender frame, the exporter evaluates the deformed mesh and stores the resulting vertex positions.

Multiple selected Mesh objects are supported. They use the same frame range and
sampling step, and each Mesh receives its own generated `.c` and `.h` file pair.

Each animation export also contains the reference frame's fixed triangles and
UV data. At runtime, the relationship is:

- the animation's reference topology provides triangles and UVs
- the animation provides the current frame's vertex positions

Conceptually:

```text
animation frame vertices
        +
reference triangles
        +
reference UVs
        ↓
     renderer
```

PSX Toolkit does **not** currently export a runtime skeletal animation system.

## Recommended Character Workflow

For a complete animated character made from several Blender objects, exporting a single joined Mesh is currently the simplest workflow.

A practical authoring workflow is:

1. Keep body parts separate while editing.
2. Preserve the editable version.
3. Create a joined export version.
4. Verify the joined model's UVs and materials.
5. Verify that Armature deformation still works correctly.
6. Export the model and animation from the joined Mesh.

Separate Mesh exports are still useful for things such as:

- weapons
- swappable equipment
- independent props
- objects that require separate rendering passes
- assets that need independent transforms

Multiple Mesh objects are therefore not inherently unsupported, but the PS1 application must manage their transforms and rendering order.

## Generated Data

Model exports contain the static data required to reconstruct the mesh:

- vertices
- triangle indices
- UV coordinates
- triangle UV indices
- counts

Animation exports contain sampled vertex positions, source frame numbers, and
the fixed reference triangles and UVs used by every exported frame.

The intended runtime relationship is:

```text
Model:
    topology + UVs

Animation:
    changing vertex positions
```

This allows the PS1 application to reuse the same triangle and UV data while changing only the vertex array for animation playback.

## PS1 Rendering Notes

The PlayStation 1 does not provide a conventional modern Z-buffer.

PSX Toolkit exports geometry and UV data, but visibility and depth ordering are the responsibility of the runtime renderer.

When rendering a 3D model, do **not** place every polygon into one fixed Ordering Table bucket.

A typical PSn00bSDK-style depth calculation looks like:

```c
gte_avsz3();
gte_stotz(&depth);
depth >>= 2;

addPrim(&ordering_table[depth], primitive);
```

The exact Ordering Table size, clipping rules, and valid depth range depend on your renderer.

Incorrect Ordering Table depth handling can cause hidden or distant polygons to overwrite visible polygons. With textured geometry, this can look very similar to corrupted or scrambled UV mapping even when the exported UV data is correct.

This is a renderer-side issue, not a PSn00bSDK or exporter UV issue.

## Textured Triangle Mapping

For a textured `POLY_FT3`, keep the projected vertex and UV corner order aligned:

```text
vertex[0] → x0/y0 → uv[0] → u0/v0
vertex[1] → x1/y1 → uv[1] → u1/v1
vertex[2] → x2/y2 → uv[2] → u2/v2
```

Vertex and UV indices are separate, but their triangle corner order must remain consistent.

## Known Limitations

This is an early beta release.

Current limitations include:

- Output/API format may still change
- Baked vertex animation only
- No runtime skeletal animation export
- No animation interpolation
- No animation blending
- No animation compression
- Limited material and multi-texture workflow
- Multi-part animated characters are currently easiest to export as one joined Mesh
- Runtime renderer implementation is not included
- Runtime texture upload is not included
- Runtime GTE setup is not included
- Runtime Ordering Table management is not included
- Runtime animation playback code is not generated automatically

## Possible Future Work

Possible future directions include:

- improved material and texture handling
- better animation metadata
- animation playback helpers
- animation compression
- improved multi-object export workflow
- additional validation and diagnostics
- a minimal PSn00bSDK example project

These are possible directions, not guaranteed features.

## Reporting Issues

Bug reports and test feedback are welcome.

When reporting an exporter issue, please include as much of the following as possible:

- Blender version
- PSX Toolkit version or commit
- model vertex/triangle information
- texture dimensions
- export settings
- whether the problem appears in generated data or only at runtime
- a minimal reproduction if possible

For rendering problems, also check the PS1-side renderer before assuming the exported data is incorrect, especially:

- Ordering Table depth
- triangle corner order
- texture page configuration
- texture dimensions
- UV index usage

## License

This repository does not currently include a license file. A license should be
specified before a stable public release.
