# PSX Toolkit

PSX Toolkit is a Blender add-on project for building tools that support a
PlayStation-era visual style. The project currently contains only the add-on
foundation; no asset-processing features have been implemented yet.

## Development environment

- Blender 4.2 or newer
- Python 3.11 or newer
- A local `.venv` created with Python 3.13.0
- Ruff for formatting and linting
- Pytest for testing

Blender uses its own bundled Python interpreter when the add-on runs. The local
virtual environment is for editor tooling and tests; development dependencies
are declared in `pyproject.toml` but are not installed automatically.

## Install or link the add-on

For a regular installation, create a ZIP archive whose top-level folder is
`psx_toolkit`. In Blender, open **Edit > Preferences > Add-ons**, choose
**Install from Disk**, select the ZIP, and enable **PSX Toolkit**.

For development, link the package directly into Blender's user add-ons folder.
On macOS with Blender 4.2, run this from the project root:

```sh
mkdir -p "$HOME/Library/Application Support/Blender/4.2/scripts/addons"
ln -s "$PWD/psx_toolkit" \
  "$HOME/Library/Application Support/Blender/4.2/scripts/addons/psx_toolkit"
```

Replace `4.2` with the Blender version being used. On Linux, the equivalent
base directory is usually `~/.config/blender/<version>/scripts/addons`; on
Windows it is usually `%APPDATA%\\Blender Foundation\\Blender\\<version>\\scripts\\addons`.
After linking, enable **PSX Toolkit** in Blender's Add-ons preferences.

## Reload during development

After editing Python files, disable and re-enable **PSX Toolkit** in
**Edit > Preferences > Add-ons**. Alternatively, enable Blender's Developer
Extras and use **Edit > Menu Search > Reload Scripts**. Restart Blender if a
module remains cached or registration state becomes inconsistent.
