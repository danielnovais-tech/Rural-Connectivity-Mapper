# Dev Setup (Windows-first)

## 1) Create and select a Python environment

- Use Python 3.12+
- Create a venv (Task): **Bootstrap: Create .venv (system python)**
- In VS Code: select the interpreter at `.venv/Scripts/python.exe`

## 2) Install deps + sanity checks

- Task: **Setup: Install deps + quick checks**

This runs `scripts/setup_environment.py` using your selected interpreter.

## 3) Daily workflow

- Lint + types: **Lint+Types: Ruff + mypy**
- Tests: **Pytest (repo)**
- Pipeline: **Pipeline: Run (default)**

## 4) ANATEL manual datasets (optional)

- Generate guide: **ANATEL: Generate download guide**
- Show priority: **ANATEL: Show priority**
- Process manual CSVs: **ANATEL: Process manual CSVs**

Manual artifacts are ignored by git (raw downloads / processed outputs), but the guide and templates stay versioned.

## 5) Debugging

Use the **Run and Debug** sidebar. Launch configs are in `.vscode/launch.json`.

## Notes on GitHub Actions status

- Old commits can stay red forever (they ran on the old code). Always check the latest run attached to the current `main` commit.
- The Actions workflow **Lint** runs `ruff` and `flake8`. The VS Code task **Lint+Types: Ruff + mypy** also runs `mypy` locally, which is not part of the default Actions lint workflow.
