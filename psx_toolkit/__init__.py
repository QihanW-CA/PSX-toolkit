"""Blender add-on entry point for PSX Toolkit."""

bl_info = {
    "name": "PSX Toolkit",
    "author": "PSX Toolkit contributors",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D",
    "description": "Tools for creating PlayStation-style assets in Blender",
    "category": "3D View",
}

_modules = ()


def register() -> None:
    """Register PSX Toolkit with Blender."""

    from . import operators, panels, properties

    global _modules
    _modules = (properties, operators, panels)
    for module in _modules:
        module.register()


def unregister() -> None:
    """Unregister PSX Toolkit from Blender."""

    for module in reversed(_modules):
        module.unregister()


if __name__ == "__main__":
    register()
