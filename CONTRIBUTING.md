# Contributing to Blender-CM3D2-Converter

Thank you for your interest in contributing to this Blender add-on.
This repository supports CM3D2/COM3D2 model, texture, material, and animation import/export in Blender.

> **All code contributions and pull requests must target the `testing` branch.**

## What to contribute

You can help with:
- adding/improving translations
- bug reports and reproducible issue descriptions
- fixes for import/export behavior
- Blender UI and operator improvements
- tests for add-on features and format handling
- documentation updates for installation or workflow

## How to contribute

1. Check open issues before starting work.
2. If you find a bug or want to request an improvement, create an issue with:
   - a clear title
   - Blender version and OS
   - steps to reproduce
   - expected behavior and actual behavior
   - any relevant file types (`.model`, `.tex`, `.mate`, `.anm`)
3. Fork the repository and create a feature branch from `testing`.
4. Make your changes on a branch named something like `fix-model-export` or `add-unit-test`.
5. Add new tests whenever you change behavior, especially for import/export or Blender-specific logic.
6. Open a pull request against the repository `testing` branch.
7. In the PR description, reference the issue and describe how to reproduce your changes.

## Development setup

This project is a Blender add-on written in Python. It targets Blender 2.8x+ API behavior and is not compatible with Blender 2.7x.
Blender 3.3 LTS is the recommended primary testing version.

### Local setup

1. Clone the repository.
2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### Blender notes

- The add-on code lives under `CM3D2 Converter/`.
- The add-on uses Blender APIs such as `bpy`, `bpy.types`, and `bpy.props`.
- Do not assume compatibility with Blender 2.7x.
- Preserve Japanese UI labels, strings, and comments. New comments, labels, and strings may be made in English, but Japanese text should never be replaces with English text.
- New UI-visible strings should have translation entries added in `CM3D2 Converter/translations/`

## Testing

Tests are located in the `test/` directory.
The repository currently uses Python `unittest` for add-on tests.

Run tests from the repository root after activating the virtual environment:
```powershell
python -m unittest discover test
```

### Test requirements

- If your changes modify any file imports/exports, include a new test in the appropriate `test_*.py` file.
- If you modify Blender-specific behavior, make sure tests still pass with the Blender environment configured in `requirements.txt`.
- Most test resources will need to be obtained on your own as they are not tracked in source control due to copyright.

## Code guidelines

- Yes, the codebase is a messy pile of spaghetti, but please avoid huge refactors as that requires lots of regression testing.
- Follow good modern coding practices where possible, even if they weren't followed before.
- Every line of any AI-generated code must be reviewed by a human. No exceptions.

## Pull request expectations

- Target the `testing` branch.
- Keep PRs focused and document the scope clearly.
- Include test results and the steps you used to verify the change.
- If a PR fixes an issue, mention the issue number.

## Reporting bugs and requesting enhancements

Use GitHub Issues to report bugs and suggest enhancements.
When reporting a bug, include:
- Blender version
- operating system
- exact steps to reproduce
- relevant file type and add-on action
- expected behavior and actual result

If you are unsure about the best approach, comment on an issue before starting a large change.

## Contact

You are more likely to get a much quicker reply if you DM @luvoido on Discord.
