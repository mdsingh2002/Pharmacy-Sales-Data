"""
CSV Extraction Module
Handles reading and initial validation of source CSV files
"""

import pandas as pd
from typing import Dict, List
from pathlib import Path
import logging


class CSVExtractor:
    """Extract data from CSV files with validation"""

    def __init__(self, data_dir: str):
        """
        Initialize CSV extractor

        Args:
            data_dir: Directory containing CSV files
        """
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger(__name__)

    def extract_file(self, filename: str, expected_columns: List[str]) -> pd.DataFrame:
        """
        Extract single CSV file with validation

        Args:
            filename: Name of CSV file
            expected_columns: List of expected column names

        Returns:
            pandas DataFrame

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If expected columns are missing
        """
        file_path = self.data_dir / filename

        # File existence check
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read CSV
        self.logger.info(f"Reading file: {file_path}")
        df = pd.read_csv(file_path)

        # Column validation
        missing_cols = set(expected_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing columns in {filename}: {missing_cols}")

        self.logger.info(f"Extracted {len(df)} rows from {filename}")

        return df

    def extract_all_sales_files(self) -> Dict[str, pd.DataFrame]:
        """
        Extract all 4 sales CSV files

        Returns:
            Dictionary with granularity as key, DataFrame as value
        """
        files = {
            'HOURLY': 'saleshourly.csv',
            'DAILY': 'salesdaily.csv',
            'WEEKLY': 'salesweekly.csv',
            'MONTHLY': 'salesmonthly.csv'
        }

        common_cols = ['datum', 'M01AB', 'M01AE', 'N02BA', 'N02BE',
                       'N05B', 'N05C', 'R03', 'R06']

        result = {}
        total_records = 0

        for granularity, filename in files.items():
            try:
                df = self.extract_file(filename, common_cols)
                df['granularity'] = granularity
                result[granularity] = df
                total_records += len(df)

                self.logger.info(
                    f"Successfully extracted {granularity} data: {len(df)} records"
                )

            except Exception as e:
                self.logger.error(f"Failed to extract {filename}: {str(e)}")
                raise

        self.logger.info(f"Total records extracted: {total_records}")

        return result

    def validate_file_structure(self, df: pd.DataFrame, granularity: str) -> bool:
        """
        Validate file structure based on granularity

        Args:
            df: DataFrame to validate
            granularity: Expected granularity (HOURLY, DAILY, WEEKLY, MONTHLY)

        Returns:
            True if valid, False otherwise
        """
        # Check for required columns based on granularity
        required_cols = ['datum', 'M01AB', 'M01AE', 'N02BA', 'N02BE',
                        'N05B', 'N05C', 'R03', 'R06']

        # Hourly and daily files have additional columns
        if granularity in ['HOURLY', 'DAILY']:
            required_cols.extend(['Year', 'Month', 'Hour', 'Weekday Name'])

        missing = set(required_cols) - set(df.columns)

        if missing:
            self.logger.warning(
                f"Missing expected columns for {granularity}: {missing}"
            )
            return False

        return True
