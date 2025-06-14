#!/usr/bin/env python3
"""
Data Processor Script

A comprehensive data processing tool that reads CSV files, validates data,
performs transformations, aggregates by category, and exports results.
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from pandas import DataFrame


class DataProcessor:
    """Main class for processing CSV data files."""
    
    def __init__(self, input_dir: str, output_dir: str, log_level: str = "INFO"):
        """
        Initialize the DataProcessor.
        
        Args:
            input_dir: Directory containing input CSV files
            output_dir: Directory for output files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging(log_level)
        self.data_frames: Dict[str, DataFrame] = {}
        self.validation_report: Dict[str, Dict[str, Any]] = {}
        
    def _setup_logging(self, log_level: str) -> None:
        """Set up logging configuration."""
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
            
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'data_processor.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def read_csv_files(self) -> None:
        """Read all CSV files from the input directory."""
        csv_files = list(self.input_dir.glob("*.csv"))
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.input_dir}")
            
        self.logger.info(f"Found {len(csv_files)} CSV files to process")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                self.data_frames[csv_file.stem] = df
                self.logger.info(f"Successfully read {csv_file.name}: {len(df)} rows")
            except Exception as e:
                self.logger.error(f"Error reading {csv_file.name}: {str(e)}")
                
    def validate_data(self) -> None:
        """Validate data in all loaded DataFrames."""
        for name, df in self.data_frames.items():
            self.logger.info(f"Validating {name}...")
            report = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "missing_values": {},
                "data_types": {},
                "validation_issues": []
            }
            
            # Check for missing values
            missing_counts = df.isnull().sum()
            for col, count in missing_counts.items():
                if count > 0:
                    report["missing_values"][col] = {
                        "count": int(count),
                        "percentage": round(count / len(df) * 100, 2)
                    }
                    
            # Document data types
            for col in df.columns:
                report["data_types"][col] = str(df[col].dtype)
                
            # Validate specific data types
            for col in df.columns:
                if 'date' in col.lower():
                    try:
                        pd.to_datetime(df[col].dropna())
                    except:
                        report["validation_issues"].append(
                            f"Column '{col}' appears to be a date but has invalid values"
                        )
                        
                if df[col].dtype == 'object':
                    # Check for unexpected numeric strings
                    numeric_strings = df[col].dropna().apply(
                        lambda x: str(x).replace('.', '').replace('-', '').isdigit()
                    )
                    if numeric_strings.sum() > len(df) * 0.8:
                        report["validation_issues"].append(
                            f"Column '{col}' contains mostly numeric strings"
                        )
                        
            self.validation_report[name] = report
            self.logger.info(f"Validation complete for {name}")
            
    def transform_data(self) -> None:
        """Perform data transformations on all DataFrames."""
        for name, df in self.data_frames.items():
            self.logger.info(f"Transforming {name}...")
            
            # Normalize date columns
            for col in df.columns:
                if 'date' in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        df[col] = df[col].dt.strftime('%Y-%m-%d')
                        self.logger.debug(f"Normalized date column: {col}")
                    except Exception as e:
                        self.logger.warning(f"Could not normalize {col}: {str(e)}")
                        
            # Clean string columns
            string_cols = df.select_dtypes(include=['object']).columns
            for col in string_cols:
                # Skip date columns we just processed
                if 'date' not in col.lower():
                    df[col] = df[col].apply(self._clean_string)
                    self.logger.debug(f"Cleaned string column: {col}")
                    
            # Remove duplicate rows
            original_len = len(df)
            df.drop_duplicates(inplace=True)
            if len(df) < original_len:
                self.logger.info(f"Removed {original_len - len(df)} duplicate rows")
                
            self.data_frames[name] = df
            
    def _clean_string(self, value: Any) -> Optional[str]:
        """Clean individual string values."""
        if pd.isna(value):
            return None
        
        # Convert to string and clean
        str_value = str(value).strip()
        
        # Remove extra whitespace
        str_value = ' '.join(str_value.split())
        
        # Remove common unwanted characters
        for char in ['\n', '\r', '\t']:
            str_value = str_value.replace(char, ' ')
            
        return str_value if str_value else None
        
    def aggregate_by_category(self, category_column: str = "category") -> DataFrame:
        """
        Aggregate data by category across all DataFrames.
        
        Args:
            category_column: Name of the category column to aggregate by
            
        Returns:
            Aggregated DataFrame
        """
        aggregated_data = []
        
        for name, df in self.data_frames.items():
            if category_column not in df.columns:
                self.logger.warning(
                    f"Category column '{category_column}' not found in {name}"
                )
                continue
                
            # Identify numeric columns for aggregation
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if not numeric_cols:
                self.logger.warning(f"No numeric columns found in {name} for aggregation")
                continue
                
            # Perform aggregation
            agg_dict = {col: ['sum', 'mean', 'count'] for col in numeric_cols}
            grouped = df.groupby(category_column).agg(agg_dict)
            
            # Flatten column names
            grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
            grouped['source_file'] = name
            grouped.reset_index(inplace=True)
            
            aggregated_data.append(grouped)
            self.logger.info(f"Aggregated {name} by {category_column}")
            
        if aggregated_data:
            return pd.concat(aggregated_data, ignore_index=True)
        else:
            return pd.DataFrame()
            
    def export_results(self, aggregated_df: Optional[DataFrame] = None) -> None:
        """Export processed data and reports to JSON and CSV formats."""
        # Export validation report
        validation_path = self.output_dir / "validation_report.json"
        with open(validation_path, 'w') as f:
            json.dump(self.validation_report, f, indent=2, default=str)
        self.logger.info(f"Exported validation report to {validation_path}")
        
        # Export processed DataFrames
        for name, df in self.data_frames.items():
            # CSV export
            csv_path = self.output_dir / f"{name}_processed.csv"
            df.to_csv(csv_path, index=False)
            self.logger.info(f"Exported {name} to CSV: {csv_path}")
            
            # JSON export
            json_path = self.output_dir / f"{name}_processed.json"
            df.to_json(json_path, orient='records', indent=2, default_handler=str)
            self.logger.info(f"Exported {name} to JSON: {json_path}")
            
        # Export aggregated data if available
        if aggregated_df is not None and not aggregated_df.empty:
            agg_csv_path = self.output_dir / "aggregated_by_category.csv"
            aggregated_df.to_csv(agg_csv_path, index=False)
            
            agg_json_path = self.output_dir / "aggregated_by_category.json"
            aggregated_df.to_json(
                agg_json_path, orient='records', indent=2, default_handler=str
            )
            self.logger.info(f"Exported aggregated data to {agg_csv_path} and {agg_json_path}")
            
    def process(self, category_column: str = "category") -> None:
        """
        Execute the complete data processing pipeline.
        
        Args:
            category_column: Column name to use for aggregation
        """
        try:
            self.logger.info("Starting data processing pipeline...")
            
            # Read CSV files
            self.read_csv_files()
            
            # Validate data
            self.validate_data()
            
            # Transform data
            self.transform_data()
            
            # Aggregate by category
            aggregated_df = self.aggregate_by_category(category_column)
            
            # Export results
            self.export_results(aggregated_df)
            
            self.logger.info("Data processing completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Processing failed: {str(e)}", exc_info=True)
            raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process CSV files with validation, transformation, and aggregation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input_data/ output_data/
  %(prog)s input_data/ output_data/ --category product_type
  %(prog)s input_data/ output_data/ --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "input_dir",
        help="Directory containing input CSV files"
    )
    
    parser.add_argument(
        "output_dir",
        help="Directory for output files"
    )
    
    parser.add_argument(
        "--category",
        default="category",
        help="Column name to use for aggregation (default: category)"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        sys.exit(1)
        
    # Create processor and run
    processor = DataProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        log_level=args.log_level
    )
    
    try:
        processor.process(category_column=args.category)
    except Exception as e:
        print(f"Processing failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Example usage when run directly
    if len(sys.argv) == 1:
        # Demo mode - create sample data and process it
        print("Running in demo mode...")
        
        # Create demo directories
        demo_input = Path("demo_input")
        demo_output = Path("demo_output")
        demo_input.mkdir(exist_ok=True)
        
        # Create sample CSV data
        sample_data = {
            "sales_data.csv": pd.DataFrame({
                "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-01"],
                "category": ["Electronics", "Electronics", "Clothing", "Clothing"],
                "product": ["Laptop", "Phone", "Shirt", "Pants"],
                "quantity": [5, 10, 20, 15],
                "price": [999.99, 599.99, 29.99, 49.99],
                "revenue": [4999.95, 5999.90, 599.80, 749.85]
            }),
            "inventory_data.csv": pd.DataFrame({
                "date": ["2024/01/01", "2024/01/02", "2024/01/03"],
                "category": ["Electronics", "Clothing", "Electronics"],
                "item_name": ["  Laptop  ", "Shirt\n", "\tPhone"],
                "stock_count": [50, 200, 75],
                "reorder_level": [10, 50, 20]
            })
        }
        
        # Save sample data
        for filename, df in sample_data.items():
            df.to_csv(demo_input / filename, index=False)
            
        print(f"Created sample data in {demo_input}/")
        
        # Process the demo data
        processor = DataProcessor(
            input_dir=str(demo_input),
            output_dir=str(demo_output),
            log_level="INFO"
        )
        
        processor.process()
        
        print(f"\nDemo complete! Check {demo_output}/ for results.")
        print("\nTo use with your own data:")
        print(f"  python {sys.argv[0]} <input_dir> <output_dir>")
    else:
        main()