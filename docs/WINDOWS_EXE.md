# Windows EXE (PyInstaller)

This repo can be packaged into a single Windows executable (`rural-mapper.exe`) using PyInstaller.

## What the EXE does

The EXE is a launcher with subcommands:

- `rural-mapper.exe cli ...` → runs the existing CLI in `main.py`
- `rural-mapper.exe pipeline ...` → runs `scripts/run_pipeline.py`
- `rural-mapper.exe web ...` → runs `app.py` (Flask)
- `rural-mapper.exe crowdsource ...` → runs `crowdsource_server.py` (Flask)
- `rural-mapper.exe dashboard ...` → runs `dashboard.py` via Streamlit
- `rural-mapper.exe blueprint` → writes `%LOCALAPPDATA%\RuralMapper\BLUEPRINT.md`

## Output directory (AppData)

When running from the EXE, outputs are written to a user-writable folder:

- `%LOCALAPPDATA%\\RuralMapper`

This path is controlled via the environment variable `RURAL_MAPPER_DATA_DIR`.

Note: you can override the blueprint output path with:

- `rural-mapper.exe blueprint -- --output <path>`

## Build prerequisites

PyInstaller may not support the newest Python versions immediately. If building fails, use Python 3.12.

Recommended build steps:

1. Create a clean venv with Python 3.12
2. Install dependencies (`requirements.txt` + build tools)
3. Build with PyInstaller using the spec

## Build command

From repo root:

- `python -m pip install -U pip pyinstaller`
- `python -m pip install -r requirements.txt`
- `python -m PyInstaller --noconfirm build/rural_mapper.spec`

Output:

- `dist\\rural-mapper.exe`

## Smoke test

From a clean folder:

- `rural-mapper.exe cli --help`
- `rural-mapper.exe pipeline --help`
- `rural-mapper.exe web`
- `rural-mapper.exe dashboard`

If any mode fails, capture the console output and iterate on `build/rural_mapper.spec` hidden imports/datas.
