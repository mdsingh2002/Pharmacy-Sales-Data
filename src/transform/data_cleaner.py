"""
Data Cleaning Module
Standardizes data types, handles missing values, and performs initial cleaning
"""

import pandas as pd
import numpy as np
from typing import List
import logging


class DataCleaner:
    """Clean and standardize sales data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def standardize_datetime(self, df: pd.DataFrame, granularity: str) -> pd.DataFrame:
        """
        Parse and standardize datetime column

        Handles different datetime formats across files:
        - Hourly: '1/2/2014 8:00'
        - Daily: '1/2/2014'
        - Weekly: '1/5/2014'
        - Monthly: '2014-01-31'

        Args:
            df: Input DataFrame
            granularity: Data granularity (HOURLY, DAILY, WEEKLY, MONTHLY)

        Returns:
            DataFrame with standardized datetime columns
        """
        df = df.copy()

        # Parse datetime
        df['sale_datetime'] = pd.to_datetime(df['datum'])

        # Extract date_key (for partitioning in BigQuery)
        df['date_key'] = df['sale_datetime'].dt.date

        # Extract temporal components
        df['year'] = df['sale_datetime'].dt.year
        df['month'] = df['sale_datetime'].dt.month

        # For hourly data, preserve hour
        if granularity == 'HOURLY':
            df['hour'] = df['sale_datetime'].dt.hour
        elif 'Hour' in df.columns:
            # Use existing hour column if available
            df['hour'] = df['Hour']
        else:
            df['hour'] = None

        # Extract weekday name
        if 'Weekday Name' in df.columns:
            df['weekday_name'] = df['Weekday Name']
        else:
            df['weekday_name'] = df['sale_datetime'].dt.day_name()

        self.logger.info(f"Standardized datetime for {granularity} data")

        return df

    def handle_missing_values(self, df: pd.DataFrame, medication_cols: List[str]) -> pd.DataFrame:
        """
        Handle missing values in medication sales columns
        Strategy: NaN -> 0 (assumption: no sale = 0 units)

        Args:
            df: Input DataFrame
            medication_cols: List of medication column names

        Returns:
            DataFrame with missing values handled
        """
        df = df.copy()

        # Count missing values before filling
        missing_counts = df[medication_cols].isna().sum()
        total_missing = missing_counts.sum()

        if total_missing > 0:
            self.logger.warning(
                f"Found {total_missing} missing values across medication columns"
            )

            # Fill with 0
            df[medication_cols] = df[medication_cols].fillna(0)

            self.logger.info(f"Filled {total_missing} missing values with 0")

        return df

    def validate_data_types(self, df: pd.DataFrame, medication_cols: List[str]) -> pd.DataFrame:
        """
        Ensure correct data types for all columns

        Args:
            df: Input DataFrame
            medication_cols: List of medication column names

        Returns:
            DataFrame with validated data types
        """
        df = df.copy()

        # Convert medication columns to float
        for col in medication_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Convert temporal columns to int (if present)
        temporal_cols = ['year', 'month', 'hour']
        for col in temporal_cols:
            if col in df.columns and df[col].notna().any():
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

        self.logger.info("Validated data types")

        return df

    def remove_duplicates(self, df: pd.DataFrame, subset_cols: List[str]) -> pd.DataFrame:
        """
        Remove duplicate records based on subset of columns

        Args:
            df: Input DataFrame
            subset_cols: Columns to check for duplicates

        Returns:
            DataFrame with duplicates removed
        """
        initial_count = len(df)
        df = df.drop_duplicates(subset=subset_cols, keep='first')

        removed = initial_count - len(df)
        if removed > 0:
            self.logger.warning(f"Removed {removed} duplicate records")
        else:
            self.logger.info("No duplicate records found")

        return df

    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names (lowercase, remove spaces)

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with cleaned column names
        """
        df = df.copy()

        # Store original column names for medication codes
        medication_cols = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']

        # Don't modify medication code column names
        for col in df.columns:
            if col not in medication_cols:
                new_col = col.lower().replace(' ', '_')
                if new_col != col:
                    df.rename(columns={col: new_col}, inplace=True)

        return df

    def handle_negative_values(self, df: pd.DataFrame, medication_cols: List[str]) -> pd.DataFrame:
        """
        Handle negative sales values (convert to 0 or flag as errors)

        Args:
            df: Input DataFrame
            medication_cols: List of medication column names

        Returns:
            DataFrame with negative values handled
        """
        df = df.copy()

        # Count negative values
        negative_mask = df[medication_cols] < 0
        negative_count = negative_mask.sum().sum()

        if negative_count > 0:
            self.logger.warning(
                f"Found {negative_count} negative sales values - converting to 0"
            )

            # Convert negative values to 0
            df[medication_cols] = df[medication_cols].clip(lower=0)

        return df
