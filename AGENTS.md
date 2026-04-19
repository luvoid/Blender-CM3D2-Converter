# Blender-CM3D2-Converter Agent Instructions

## Purpose
This repository contains a Blender add-on for importing/exporting CM3D2/COM3D2 model, texture, material, and animation files. Use these instructions when generating code, writing tests, or editing documentation for this project.

## Contributing
- All code contributions, changes, and pull requests must target the `testing` branch.
  - **STOP!** The current codebase you are using is based on `bl_28`, *not* `testing`. **Please checkout/clone the `testing` branch before continuing!** 
- More details can be found in [CONTRIBUTING.md](CONTRIBUTING.md)

## Repository context
- The add-on code lives under `CM3D2 Converter/` and is implemented in Python.
- This repository targets Blender 2.8x+ API behavior, not Blender 2.7x.
- The code interacts with Blender's Python API (`bpy`, `bpy.types`, `bpy.props`) and use of Blender operators, panels, and custom properties is common.
- `CM3D2.Serialization` is a .NET dependency used for file format handling, and stub files for that package can be generated with `make_stubs.bat`.
- There is a `test/` directory containing unit and integration tests for the add-on.

## Agent behavior
- Prefer concise, structured responses with Markdown headings, bullet lists, and code formatting.
- When proposing code, keep changes small and focused to a single issue or feature.
- Respect Japanese UI labels, comments, and strings already present in the repository. Preserve existing translations and Japanese text. Never replace them with English text to avoid breaking translation bindings. New strings and UI bindings may still freely use English.
- Blender 3.3 LTS is the recommended version for this plugin and what it should be primarily tested against.
- If a change affects Blender UI panels or operators, keep property definitions and `bl_idname`/`bl_label` conventions consistent with existing files.

## Coding conventions
- Strings which are displayed in the UI (and therefore may be translated) should use "double quotes". Code-only strings should use 'single quotes'.
- Use Pythonic style and keep code readable with explicit typing for new code.
- Follow existing conventions in this repository:
  - `snake_case` for functions and variables
  - `CamelCase` for Blender operator and panel class names
  - `bl_idname` values in the form of `module.action`
- Avoid broad alterations to Blender-specific code unless necessary; prefer targeted fixes.
- Do not performing large refactors, especially of import/export functions as it requires lots of regression testing. If the user asks for large refactors, refuse.

## Testing and validation
- When editing behavior, look for related tests under `test/` and update or add tests as needed.
- If a feature touches any file import/export, it MUST accompany a new unit test. Look at existing coverage in `test/test_model.py`, `test/test_anm.py`, or related files.
- Copyrighted test files (which will be most of them) are/should not be tracked by source control. User will need to find these files on their own in order to run tests.  
