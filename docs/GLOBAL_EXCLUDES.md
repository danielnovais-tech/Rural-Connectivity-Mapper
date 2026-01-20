# Global Excludes (Blackbox-style)

You can configure global file/folder exclusion patterns that apply to all projects (so you don’t need to repeat them in every project-specific ignore file).

## Location

Create a JSON file at:

- `~/.blackbox/settings.json`

On Windows, `~` expands to your user profile directory.

## Schema

Example:

```json
{
  "globalExcludes": [
    "dist/",
    "build/",
    ".DS_Store",
    "*.pyc",
    "__pycache__/"
  ]
}
```

## Usage in code

Python utilities are implemented in:

- `src/utils/report_utils.py`

Relevant helpers:

- `getCustomExcludes()` reads `globalExcludes` from `~/.blackbox/settings.json`.
- `getCombinedExcludes(project_excludes=...)` merges built-ins (e.g. `.git/`, `node_modules/`) with project + global excludes.

Optional testing override:

- Set `BLACKBOX_SETTINGS_PATH` to point to a custom settings file.
