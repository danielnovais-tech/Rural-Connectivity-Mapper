"""Data utilities for loading, saving, and managing data files."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def load_data(filepath: str) -> list[dict]:
    """Load JSON data from file.

    Args:
        filepath: Path to JSON file

    Returns:
        List[Dict]: Loaded data as list of dictionaries

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        path = Path(filepath)

        if not path.exists():
            logger.warning(f"File not found: {filepath}. Returning empty list.")
            return []
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Successfully loaded {len(data)} records from {filepath}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading data from {filepath}: {e}")
        raise


def save_data(filepath: str, data: list[dict]) -> None:
    """Save data to JSON file.

    Args:
        filepath: Path to save JSON file
        data: List of dictionaries to save

    Raises:
        OSError: If file cannot be written
    """
    try:
        path = Path(filepath)

        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully saved {len(data)} records to {filepath}")

    except Exception as e:
        logger.error(f"Error saving data to {filepath}: {e}")
        raise


def backup_data(filepath: str) -> str:
    """Create a timestamped backup of a data file.

    Args:
        filepath: Path to file to backup

    Returns:
        str: Path to backup file

    Raises:
        FileNotFoundError: If source file doesn't exist
    """
    try:
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {filepath}")

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.parent / f"{path.stem}_backup_{timestamp}{path.suffix}"

        # Copy file to backup location
        shutil.copy2(path, backup_path)

        logger.info(f"Created backup: {backup_path}")
        return str(backup_path)

    except Exception as e:
        logger.error(f"Error creating backup of {filepath}: {e}")
        raise
