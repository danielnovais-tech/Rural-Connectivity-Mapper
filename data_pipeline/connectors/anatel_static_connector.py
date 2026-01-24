#!/usr/bin/env python3
"""
ANATEL Static Connector

This connector reads CSV files from the manual data directory, converts them to 
Parquet format for efficient storage and processing, and generates a validation report.

Usage:
    python data_pipeline/connectors/anatel_static_connector.py

Input:
    - CSV files from data/manual/ directory

Output:
    - Parquet files in data/bronze/anatel/ directory
    - JSON validation report
"""

import json
import logging
import traceback
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ANATELStaticConnector:
    """Connector for processing ANATEL static CSV data files."""
    
    def __init__(
        self, 
        input_dir: str = "data/manual",
        output_dir: str = "data/bronze/anatel"
    ):
        """
        Initialize the ANATEL Static Connector.
        
        Args:
            input_dir: Directory containing input CSV files
            output_dir: Directory for output Parquet files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Report data
        self.report = {
            "connector": "ANATEL Static Connector",
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "files_processed": [],
            "summary": {
                "total_files": 0,
                "successful": 0,
                "failed": 0,
                "total_records": 0
            },
            "errors": []
        }
    
    def find_csv_files(self) -> List[Path]:
        """
        Find all CSV files in the input directory.
        
        Returns:
            List of Path objects for CSV files
        """
        if not self.input_dir.exists():
            print(f"⚠️  Input directory does not exist: {self.input_dir}")
            return []
        
        csv_files = list(self.input_dir.glob("*.csv"))
        print(f"📁 Found {len(csv_files)} CSV file(s) in {self.input_dir}")
        return csv_files
    
    def validate_dataframe(self, df: pd.DataFrame, filename: str) -> Tuple[bool, List[str]]:
        """
        Validate the loaded DataFrame.
        
        Args:
            df: DataFrame to validate
            filename: Name of the source file (for error reporting)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if DataFrame is empty
        if df.empty:
            errors.append(f"DataFrame is empty")
            return False, errors
        
        # Required fields for ANATEL backhaul data
        required_fields = ['latitude', 'longitude']
        
        # Check for required fields
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Check for null values in critical fields
        for field in required_fields:
            if field in df.columns:
                null_count = df[field].isnull().sum()
                if null_count > 0:
                    errors.append(f"Field '{field}' has {null_count} null values")
        
        # Validate coordinate ranges where applicable
        if 'latitude' in df.columns:
            lat_series = pd.to_numeric(df['latitude'], errors='coerce')
            # Count non-numeric values (originally non-null but became NaN)
            non_numeric_lat = (~df['latitude'].isnull()) & (lat_series.isnull())
            non_numeric_lat_count = non_numeric_lat.sum()
            if non_numeric_lat_count > 0:
                errors.append(
                    f"Field 'latitude' has {non_numeric_lat_count} non-numeric values"
                )
            # Count out-of-range latitude values (-90 to 90)
            out_of_range_lat = lat_series.notnull() & ((lat_series < -90) | (lat_series > 90))
            out_of_range_lat_count = out_of_range_lat.sum()
            if out_of_range_lat_count > 0:
                errors.append(
                    f"Field 'latitude' has {out_of_range_lat_count} values outside [-90, 90]"
                )
        
        if 'longitude' in df.columns:
            lon_series = pd.to_numeric(df['longitude'], errors='coerce')
            # Count non-numeric values (originally non-null but became NaN)
            non_numeric_lon = (~df['longitude'].isnull()) & (lon_series.isnull())
            non_numeric_lon_count = non_numeric_lon.sum()
            if non_numeric_lon_count > 0:
                errors.append(
                    f"Field 'longitude' has {non_numeric_lon_count} non-numeric values"
                )
            # Count out-of-range longitude values (-180 to 180)
            out_of_range_lon = lon_series.notnull() & ((lon_series < -180) | (lon_series > 180))
            out_of_range_lon_count = out_of_range_lon.sum()
            if out_of_range_lon_count > 0:
                errors.append(
                    f"Field 'longitude' has {out_of_range_lon_count} values outside [-180, 180]"
                )
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def process_csv_file(self, csv_file: Path) -> Dict:
        """
        Process a single CSV file: read, validate, and convert to Parquet.
        
        Args:
            csv_file: Path to the CSV file
            
        Returns:
            Dictionary with processing results
        """
        result = {
            "filename": csv_file.name,
            "status": "unknown",
            "records_processed": 0,
            "output_file": None,
            "errors": []
        }
        
        try:
            print(f"\n📄 Processing: {csv_file.name}")
            
            # Read CSV file with explicit encoding for consistent behavior
            df = pd.read_csv(csv_file, encoding="utf-8")
            print(f"   ✓ Read {len(df)} records")
            print(f"   ✓ Columns: {list(df.columns)}")
            
            # Validate DataFrame
            is_valid, validation_errors = self.validate_dataframe(df, csv_file.name)
            
            if not is_valid:
                result["status"] = "failed"
                result["errors"] = validation_errors
                print(f"   ✗ Validation failed:")
                for error in validation_errors:
                    print(f"      - {error}")
                return result
            
            print(f"   ✓ Validation passed")
            
            # Generate output filename
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_filename = f"{csv_file.stem}_{timestamp}.parquet"
            output_path = self.output_dir / output_filename
            
            # Convert to Parquet
            df.to_parquet(output_path, index=False, engine='pyarrow')
            print(f"   ✓ Saved to: {output_path}")
            
            # Update result
            result["status"] = "success"
            result["records_processed"] = len(df)
            result["output_file"] = str(output_path)
            
            # Add basic statistics (exclude sample record for privacy/security)
            result["statistics"] = {
                "total_records": len(df),
                "columns": list(df.columns)
            }
            
        except FileNotFoundError as e:
            result["status"] = "failed"
            result["errors"] = [f"File not found: {str(e)}"]
            logger.error(f"File not found: {csv_file}: {e}")
            print(f"   ✗ Error: File not found - {e}")
        except pd.errors.ParserError as e:
            result["status"] = "failed"
            result["errors"] = [f"CSV parsing error: {str(e)}"]
            logger.error(f"CSV parsing error in {csv_file}: {e}")
            print(f"   ✗ Error: CSV parsing failed - {e}")
        except Exception as e:
            result["status"] = "failed"
            result["errors"] = [str(e)]
            logger.error(f"Unexpected error processing {csv_file}: {e}")
            logger.debug(traceback.format_exc())
            print(f"   ✗ Error: {e}")
        
        return result
    
    def process_all(self) -> Dict:
        """
        Process all CSV files in the input directory.
        
        Returns:
            Processing report dictionary
        """
        print("=" * 70)
        print("🚀 ANATEL Static Connector - Starting Processing")
        print("=" * 70)
        
        # Find CSV files
        csv_files = self.find_csv_files()
        self.report["summary"]["total_files"] = len(csv_files)
        
        if not csv_files:
            print("\n⚠️  No CSV files found to process")
            return self.report
        
        # Process each file
        for csv_file in csv_files:
            result = self.process_csv_file(csv_file)
            self.report["files_processed"].append(result)
            
            if result["status"] == "success":
                self.report["summary"]["successful"] += 1
                self.report["summary"]["total_records"] += result["records_processed"]
            else:
                self.report["summary"]["failed"] += 1
                self.report["errors"].extend(result["errors"])
        
        # Generate summary
        print("\n" + "=" * 70)
        print("📊 Processing Summary")
        print("=" * 70)
        print(f"Total files: {self.report['summary']['total_files']}")
        print(f"Successful: {self.report['summary']['successful']}")
        print(f"Failed: {self.report['summary']['failed']}")
        print(f"Total records processed: {self.report['summary']['total_records']}")
        
        # Save report
        report_filename = f"anatel_processing_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.output_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Report saved to: {report_path}")
        print("=" * 70)
        
        return self.report


def main():
    """Main execution function."""
    # Initialize connector
    connector = ANATELStaticConnector()
    
    # Process all files
    report = connector.process_all()
    
    # Exit with appropriate code
    if report["summary"]["failed"] > 0:
        print("\n⚠️  Some files failed to process. Check the report for details.")
        exit(1)
    elif report["summary"]["successful"] == 0:
        print("\n⚠️  No files were processed.")
        exit(1)
    else:
        print("\n✅ All files processed successfully!")
        exit(0)


if __name__ == "__main__":
    main()
