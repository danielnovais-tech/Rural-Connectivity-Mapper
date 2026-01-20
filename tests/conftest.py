"""Pytest configuration file."""

import sys
from pathlib import Path

# Add the parent directory to Python path so we can import app and src modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
