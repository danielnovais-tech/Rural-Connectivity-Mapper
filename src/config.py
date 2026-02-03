"""Configuration constants for Rural Connectivity Mapper."""

from __future__ import annotations

import os
from pathlib import Path

# Application version
APP_VERSION = "1.0.0-beta"

# Data storage
_REPO_ROOT = Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    """Return a writable data directory.

    Default behavior is repo-local (`src/data`). When `RURAL_MAPPER_DATA_DIR` is
    set (e.g., by the Windows EXE launcher), that directory is used instead.
    """

    env = os.environ.get("RURAL_MAPPER_DATA_DIR")
    if env:
        return Path(env)
    return _REPO_ROOT / "src" / "data"


# Backwards-compatible string path used across the repo
DATA_FILE_PATH = str(get_data_dir() / "pontos.json")

# API Configuration
DEFAULT_API_HOST = '0.0.0.0'
DEFAULT_API_PORT = 5000

# Known providers
KNOWN_PROVIDERS = [
    'Starlink', 'Viasat', 'HughesNet', 'Claro', 'Vivo', 
    'TIM', 'Oi', 'Various', 'Unknown', 'Other'
]
