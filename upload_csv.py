#!/usr/bin/env python3
"""
CSV Upload Script for Rural Connectivity Mapper 2026

Standalone script for uploading and validating speedtest data from CSV files.
Designed for low barrier to entry - ideal for contributors and rural testers.

Usage:
    python upload_csv.py example_speedtests.csv
    python upload_csv.py my_speedtests.csv --output custom_data.json
    python upload_csv.py --help

Required CSV Columns:
    - timestamp: ISO format datetime (e.g., 2026-01-15T10:30:00)
    - latitude: Latitude coordinate (-90 to 90)
    - longitude: Longitude coordinate (-180 to 180)
    - download: Download speed in Mbps (positive number)
    - upload: Upload speed in Mbps (positive number)

Optional CSV Columns:
    - id: Unique identifier for the point
    - city: City name
    - provider: Internet service provider
    - latency: Latency in milliseconds
    - jitter: Jitter in milliseconds
    - packet_loss: Packet loss percentage
"""

import argparse  # noqa: I001
import csv
import json
import sys
from pathlib import Path
from datetime import datetime


# Schema validation constants
REQUIRED_FIELDS = ["timestamp", "latitude", "longitude", "download", "upload"]
OPTIONAL_FIELDS = ["id", "city", "provider", "latency", "jitter", "packet_loss"]
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

# Coordinate validation ranges
LATITUDE_MIN = -90
LATITUDE_MAX = 90
LONGITUDE_MIN = -180
LONGITUDE_MAX = 180

# Error reporting constants
MAX_ERRORS_DISPLAYED = 20
CSV_HEADER_ROW: int = 1  # Row 1 is header, data starts at row 2


def validate_timestamp(timestamp_str: str) -> tuple[bool, str]:
    """Validate timestamp format.

    Args:
        timestamp_str: Timestamp string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Try parsing ISO format
        # Note: replace('Z', '+00:00') handles UTC timezone indicator 'Z' for ISO 8601 compatibility
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return True, ""
    except (ValueError, AttributeError):
        return False, (f"Invalid timestamp format: '{timestamp_str}'. Expected ISO format (e.g., 2026-01-15T10:30:00)")


def validate_coordinate(value: str, coord_type: str) -> tuple[bool, str]:
    """Validate latitude or longitude.

    Args:
        value: Coordinate value to validate
        coord_type: Either 'latitude' or 'longitude'

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        coord = float(value)

        if coord_type == "latitude":
            if coord < LATITUDE_MIN or coord > LATITUDE_MAX:
                return False, f"Latitude must be between {LATITUDE_MIN} and {LATITUDE_MAX}, got {coord}"
        elif coord_type == "longitude":
            if coord < LONGITUDE_MIN or coord > LONGITUDE_MAX:
                return False, f"Longitude must be between {LONGITUDE_MIN} and {LONGITUDE_MAX}, got {coord}"

        return True, ""
    except (ValueError, TypeError):
        return False, f"Invalid {coord_type}: '{value}'. Must be a number"


def validate_speed(value: str, speed_type: str) -> tuple[bool, str]:
    """Validate download or upload speed.

    Args:
        value: Speed value to validate
        speed_type: Either 'download' or 'upload'
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        speed = float(value)
        if speed < 0:
            return False, f"{speed_type.capitalize()} speed must be positive, got {speed}"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Invalid {speed_type} speed: '{value}'. Must be a number"


def validate_optional_numeric(value: str, field_name: str) -> tuple[bool, str]:
    """Validate optional numeric fields.

    Args:
        value: Value to validate
        field_name: Name of the field

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or value.strip() == "":
        return True, ""  # Optional field can be empty

    try:
        num = float(value)
        if num < 0:
            return False, f"{field_name.capitalize()} must be positive, got {num}"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Invalid {field_name}: '{value}'. Must be a number"


def validate_fields(row: dict[str, str], row_num: int) -> list[str]:
    """Validate all fields in a row.

    Args:
        row: Dictionary representing a CSV row
        row_num: Row number for error reporting

    Returns:
        List of validation errors
    """
    errors: list[str] = []

    # Validate timestamp
    is_valid, error = validate_timestamp(row["timestamp"])
    if not is_valid:
        errors.append(f"Row {row_num}: {error}")

    # Validate latitude
    is_valid, error = validate_coordinate(row["latitude"], "latitude")
    if not is_valid:
        errors.append(f"Row {row_num}: {error}")

    # Validate longitude
    is_valid, error = validate_coordinate(row["longitude"], "longitude")
    if not is_valid:
        errors.append(f"Row {row_num}: {error}")

    # Validate download speed
    is_valid, error = validate_speed(row["download"], "download")
    if not is_valid:
        errors.append(f"Row {row_num}: {error}")

    # Validate upload speed
    is_valid, error = validate_speed(row["upload"], "upload")
    if not is_valid:
        errors.append(f"Row {row_num}: {error}")

    # Validate optional numeric fields
    for field in ["latency", "jitter", "packet_loss"]:
        if field in row:
            is_valid, error = validate_optional_numeric(row.get(field, ""), field)
            if not is_valid:
                errors.append(f"Row {row_num}: {error}")

    return errors


def validate_row(row: dict[str, str], row_num: int) -> tuple[bool, list[str]]:
    """Validate a single CSV row.

    Args:
        row: Dictionary representing a CSV row
        row_num: Row number for error reporting

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: list[str] = []

    # Check required fields exist
    for field in REQUIRED_FIELDS:
        if field not in row or not row[field]:
            errors.append(f"Row {row_num}: Missing required field '{field}'")

    if errors:
        return False, errors

    # Validate all fields
    errors = validate_fields(row, row_num)

    return len(errors) == 0, errors


def process_csv_row(
    row: dict[str, str],
    row_num: int,
    stats: dict[str, int | dict[str, int]],
    valid_rows: list[dict[str, str]],
    all_errors: list[str],
) -> None:
    """Process a single CSV row and update statistics.

    Args:
        row: Dictionary representing a CSV row
        row_num: Row number for error reporting
        stats: Statistics dictionary to update
        valid_rows: List to append valid rows to
        all_errors: List to append errors to
    """
    assert isinstance(stats["total_rows"], int)
    stats["total_rows"] += 1
    is_valid, errors = validate_row(row, row_num)

    if is_valid:
        # Track missing optional fields
        for field in OPTIONAL_FIELDS:
            if field not in row or not row[field]:
                assert isinstance(stats["missing_optional_fields"], dict)
                stats["missing_optional_fields"][field] = stats["missing_optional_fields"].get(field, 0) + 1

        valid_rows.append(row)
        assert isinstance(stats["valid_rows"], int)
        stats["valid_rows"] += 1
    else:
        all_errors.extend(errors)
        assert isinstance(stats["invalid_rows"], int)
        stats["invalid_rows"] += 1


def load_and_validate_csv(csv_path: str) -> tuple[list[dict[str, str]], list[str], dict[str, int | dict[str, int]]]:
    """Load and validate CSV file.

    Args:
        csv_path: Path to CSV file

    Returns:
        Tuple of (valid_rows, errors, statistics)
    """
    valid_rows: list[dict[str, str]] = []
    all_errors: list[str] = []
    stats: dict[str, int | dict[str, int]] = {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "missing_optional_fields": {},
    }
    # Type assertions for stats counters
    assert isinstance(stats["total_rows"], int)
    assert isinstance(stats["valid_rows"], int)
    assert isinstance(stats["invalid_rows"], int)
    assert isinstance(stats["missing_optional_fields"], dict)

    try:
        with open(csv_path, "r", encoding="utf-8") as f:  # noqa: UP015
            reader = csv.DictReader(f)

            # Check if required fields are in header
            if not reader.fieldnames:
                return [], ["CSV file is empty or has no header"], stats

            missing_required = set(REQUIRED_FIELDS) - set(reader.fieldnames)
            if missing_required:
                return [], [f"CSV header missing required fields: {', '.join(missing_required)}"], stats

            # Process each row
            for row_num, row in enumerate(reader, start=2):
                process_csv_row(row, row_num, stats, valid_rows, all_errors)

        return valid_rows, all_errors, stats

    except FileNotFoundError:
        return [], [f"File not found: {csv_path}"], stats
    except (IOError, OSError, csv.Error, UnicodeDecodeError) as e:  # noqa: UP024
        return [], [f"Error reading CSV file: {str(e)}"], stats


def convert_to_json(rows: list[dict[str, str]]) -> list[dict[str, str | float]]:
    """Convert CSV rows to JSON format.

    Args:
        rows: List of validated CSV rows

    Returns:
        List of dictionaries in JSON format
    """
    json_data: list[dict[str, str | float]] = []

    for row in rows:
        entry: dict[str, str | float] = {
            "timestamp": row["timestamp"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "download": float(row["download"]),
            "upload": float(row["upload"]),
        }

        # Add optional fields if present
        if row.get("id"):
            entry["id"] = row["id"]
        if row.get("city"):
            entry["city"] = row["city"]
        if row.get("provider"):
            entry["provider"] = row["provider"]
        if row.get("latency"):
            entry["latency"] = float(row["latency"])
        if row.get("jitter"):
            entry["jitter"] = float(row["jitter"])
        if row.get("packet_loss"):
            entry["packet_loss"] = float(row["packet_loss"])

        json_data.append(entry)

    return json_data


def save_json(data: list[dict[str, str | float]], output_path: str) -> None:
    """Save data to JSON file.

    Args:
        data: List of dictionaries to save
        output_path: Path to output JSON file
    """
    # Create directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def print_validation_report(stats: dict[str, int | dict[str, int]], errors: list[str], verbose: bool = False) -> None:
    """Print validation report.

    Args:
        stats: Statistics dictionary
        errors: List of validation errors
        verbose: Whether to print detailed error messages
    """
    print("\n" + "=" * 80)
    print("CSV VALIDATION REPORT")
    print("=" * 80)
    print(f"\nTotal rows processed: {stats['total_rows']}")
    print(f"Valid rows: {stats['valid_rows']}")
    print(f"Invalid rows: {stats['invalid_rows']}")

    missing_fields = stats["missing_optional_fields"]
    if missing_fields and isinstance(missing_fields, dict):
        print("\nOptional fields summary:")
        for field, count in missing_fields.items():
            print(f"  - {field}: missing in {count} row(s)")

    if errors:
        print(f"\n[WARNING] Found {len(errors)} validation error(s):")
        if verbose:
            for error in errors[:MAX_ERRORS_DISPLAYED]:
                print(f"  - {error}")
            if len(errors) > MAX_ERRORS_DISPLAYED:
                print(f"  ... and {len(errors) - MAX_ERRORS_DISPLAYED} more error(s)")
        else:
            print("  (Use --verbose to see detailed error messages)")

    print("=" * 80 + "\n")


def main():
    """Main entry point for CSV upload script."""
    parser = argparse.ArgumentParser(
        description="CSV Upload Script for Rural Connectivity Mapper 2026",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upload_csv.py example_speedtests.csv
  python upload_csv.py my_data.csv --output results.json
  python upload_csv.py data.csv --verbose --dry-run

Required CSV columns:
  timestamp, latitude, longitude, download, upload

Optional CSV columns:
  id, city, provider, latency, jitter, packet_loss
        """,
    )

    parser.add_argument("csv_file", help="Path to CSV file to upload")

    parser.add_argument(
        "--output", "-o", default="speedtest_data.json", help="Output JSON file path (default: speedtest_data.json)"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed validation error messages")

    parser.add_argument("--dry-run", action="store_true", help="Validate CSV without saving output file")

    args = parser.parse_args()

    # Print header
    print("\n*** Rural Connectivity Mapper 2026 - CSV Upload Script ***")
    print(f"Input: {args.csv_file}")
    if not args.dry_run:
        print(f"Output: {args.output}")
    else:
        print("Mode: Dry-run (validation only)")

    # Load and validate CSV
    print("\nValidating CSV file...")
    valid_rows, errors, stats = load_and_validate_csv(args.csv_file)

    # Print validation report
    print_validation_report(stats, errors, args.verbose)

    # Exit if there are errors
    if errors:
        print("[ERROR] Validation failed. Please fix the errors above and try again.\n")
        sys.exit(1)

    if stats["valid_rows"] == 0:
        print("[ERROR] No valid rows found in CSV file.\n")
        sys.exit(1)

    # Convert to JSON format
    json_data = convert_to_json(valid_rows)

    # Save to file unless dry-run
    if not args.dry_run:
        print(f"Saving {len(json_data)} record(s) to {args.output}...")
        save_json(json_data, args.output)
        print(f"[SUCCESS] Successfully saved data to {args.output}")
    else:
        print("[SUCCESS] Validation successful! (Dry-run mode - no file saved)")

    print("\n*** CSV upload completed successfully! ***\n")


if __name__ == "__main__":
    main()
