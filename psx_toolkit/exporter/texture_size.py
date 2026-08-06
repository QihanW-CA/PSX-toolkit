"""Resolve and validate texture dimensions without importing Blender."""

MAX_TEXTURE_DIMENSION = 256


class TextureSizeError(ValueError):
    """Raised when texture dimensions cannot be used for PS1 UV export."""


def validate_texture_size(width: int, height: int) -> tuple[int, int]:
    """Validate dimensions supported by the uint8_t UV representation."""

    width = int(width)
    height = int(height)
    if width < 1:
        raise TextureSizeError("Texture width must be at least 1 pixel.")
    if height < 1:
        raise TextureSizeError("Texture height must be at least 1 pixel.")
    if width > MAX_TEXTURE_DIMENSION:
        raise TextureSizeError("Texture width cannot exceed 256 pixels.")
    if height > MAX_TEXTURE_DIMENSION:
        raise TextureSizeError("Texture height cannot exceed 256 pixels.")
    return width, height


def resolve_texture_size(settings) -> tuple[int, int]:
    """Resolve dimensions from an explicit image or manual settings."""

    if settings.texture_size_source == "MATERIAL":
        image = settings.texture_image
        if image is None:
            raise TextureSizeError("Select a texture image before exporting.")
        return validate_texture_size(image.size[0], image.size[1])
    if settings.texture_size_source == "MANUAL":
        return validate_texture_size(
            settings.texture_width,
            settings.texture_height,
        )
    raise TextureSizeError(
        f"Unsupported texture-size source: {settings.texture_size_source}"
    )
