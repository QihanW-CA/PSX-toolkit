"""Main PSX Toolkit panel in the 3D Viewport sidebar."""

import bpy


class PSXTOOLKIT_PT_main_panel(bpy.types.Panel):
    """Display the entry point for PSX Toolkit operations."""

    bl_idname = "PSXTOOLKIT_PT_main_panel"
    bl_label = "PSX Toolkit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PSX Toolkit"

    def draw(self, context: bpy.types.Context) -> None:
        """Draw the PSX Toolkit controls."""

        settings = context.scene.psx_toolkit_export_settings
        box = self.layout.box()
        box.label(text="Model Output")
        box.operator(
            "psx_toolkit.prepare_export",
            text="Prepare PSX Export",
        )

        box.label(text="Output Folder:")
        box.prop(settings, "output_directory", text="")

        box.label(text="File Name:")
        box.prop(settings, "output_filename", text="")
        box.prop(settings, "export_scale")
        box.prop(settings, "coordinate_space")

        texture_box = box.box()
        texture_box.label(text="Texture Size")
        texture_box.prop(settings, "texture_size_source", text="Source")
        if settings.texture_size_source == "MATERIAL":
            texture_box.prop(settings, "texture_image", text="Texture")
            image = settings.texture_image
            if image is None:
                texture_box.label(text="Detected Size: No image selected")
            else:
                texture_box.label(
                    text=f"Detected Size: {image.size[0]} × {image.size[1]}"
                )
        else:
            texture_box.prop(settings, "texture_width")
            texture_box.prop(settings, "texture_height")
        texture_box.prop(settings, "flip_v")

        box.operator(
            "psx_toolkit.export_model",
            text="Export PS1 Model",
        )

        animation_box = self.layout.box()
        animation_box.label(text="Animation Output")
        animation_box.prop(settings, "animation_name")
        animation_box.prop(settings, "animation_start_frame")
        animation_box.prop(settings, "animation_end_frame")
        animation_box.prop(settings, "animation_frame_step")
        selected_mesh_count = sum(
            selected_object.type == "MESH"
            for selected_object in context.selected_objects
        )
        animation_box.label(text=f"Selected Meshes: {selected_mesh_count}")
        animation_box.operator(
            "psx_toolkit.export_animation",
            text="Export Animation",
        )
