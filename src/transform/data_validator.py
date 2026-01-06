"""
Data Quality Validation Module
Performs comprehensive data quality checks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging


class DataValidator:
    """Validate data quality and flag issues"""

    def __init__(self, config: Dict):
        """
        Initialize data validator

        Args:
            config: Data quality configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.validation_report = []

    def validate_completeness(self, df: pd.DataFrame,
                             required_cols: List[str]) -> Tuple[bool, Dict]:
        """
        Check for missing values in required columns

        Args:
            df: DataFrame to validate
            required_cols: List of required column names

        Returns:
            Tuple of (is_valid, missing_report)
        """
        missing_report = {}

        for col in required_cols:
            if col not in df.columns:
                self.logger.error(f"Required column missing: {col}")
                missing_report[col] = {
                    'missing_count': len(df),
                    'missing_pct': 100.0
                }
                continue

            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100

            missing_report[col] = {
                'missing_count': int(missing_count),
                'missing_pct': float(missing_pct)
            }

            if missing_pct > self.config.get('max_missing_pct', 5.0):
                self.logger.error(
                    f"Column {col} has {missing_pct:.2f}% missing values "
                    f"(threshold: {self.config.get('max_missing_pct', 5.0)}%)"
                )

        is_valid = all(
            r['missing_pct'] <= self.config.get('max_missing_pct', 5.0)
            for r in missing_report.values()
        )

        self.validation_report.append({
            'check': 'completeness',
            'is_valid': is_valid,
            'details': missing_report
        })

        return is_valid, missing_report

    def validate_duplicates(self, df: pd.DataFrame,
                           subset_cols: List[str]) -> Tuple[bool, int]:
        """
        Check for duplicate records

        Args:
            df: DataFrame to validate
            subset_cols: Columns to check for duplicates

        Returns:
            Tuple of (is_valid, duplicate_count)
        """
        dup_count = df.duplicated(subset=subset_cols).sum()
        dup_pct = (dup_count / len(df)) * 100

        if dup_pct > self.config.get('max_duplicate_pct', 0.1):
            self.logger.warning(
                f"Found {dup_count} duplicates ({dup_pct:.2f}%)"
            )
            is_valid = False
        else:
            is_valid = True

        self.validation_report.append({
            'check': 'duplicates',
            'is_valid': is_valid,
            'details': {
                'duplicate_count': int(dup_count),
                'duplicate_pct': float(dup_pct)
            }
        })

        return is_valid, int(dup_count)

    def detect_outliers(self, df: pd.DataFrame,
                       column: str = 'sales_quantity') -> pd.DataFrame:
        """
        Detect outliers using IQR method
        Flags outliers but doesn't remove them

        Args:
            df: DataFrame to check
            column: Column to check for outliers

        Returns:
            DataFrame with is_outlier and outlier_score columns
        """
        df = df.copy()

        # Calculate IQR
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        # Flag outliers
        df['is_outlier'] = (
            (df[column] < lower_bound) |
            (df[column] > upper_bound)
        )

        # Calculate outlier score (z-score)
        mean = df[column].mean()
        std = df[column].std()

        if std > 0:
            df['outlier_score'] = np.abs((df[column] - mean) / std)
        else:
            df['outlier_score'] = 0.0

        outlier_count = df['is_outlier'].sum()
        outlier_pct = (outlier_count / len(df)) * 100

        self.logger.info(
            f"Detected {outlier_count} outliers ({outlier_pct:.2f}%) "
            f"in {column}"
        )

        self.validation_report.append({
            'check': 'outliers',
            'is_valid': True,  # Outliers don't fail validation, just flagged
            'details': {
                'outlier_count': int(outlier_count),
                'outlier_pct': float(outlier_pct),
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound)
            }
        })

        return df

    def validate_range(self, df: pd.DataFrame,
                      column: str, min_val: float,
                      max_val: float) -> Tuple[bool, int]:
        """
        Validate that values are within expected range

        Args:
            df: DataFrame to validate
            column: Column to check
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Tuple of (is_valid, out_of_range_count)
        """
        if column not in df.columns:
            self.logger.warning(f"Column {column} not found for range validation")
            return True, 0

        out_of_range = (
            (df[column] < min_val) |
            (df[column] > max_val)
        ).sum()

        out_of_range_pct = (out_of_range / len(df)) * 100

        if out_of_range > 0:
            self.logger.warning(
                f"{out_of_range} values in {column} outside range "
                f"[{min_val}, {max_val}] ({out_of_range_pct:.2f}%)"
            )
            is_valid = False
        else:
            is_valid = True

        self.validation_report.append({
            'check': f'range_{column}',
            'is_valid': is_valid,
            'details': {
                'out_of_range_count': int(out_of_range),
                'out_of_range_pct': float(out_of_range_pct),
                'min_val': min_val,
                'max_val': max_val
            }
        })

        return is_valid, int(out_of_range)

    def validate_categorical(self, df: pd.DataFrame,
                            column: str,
                            allowed_values: List[str]) -> Tuple[bool, int]:
        """
        Validate categorical column values

        Args:
            df: DataFrame to validate
            column: Column to check
            allowed_values: List of allowed values

        Returns:
            Tuple of (is_valid, invalid_count)
        """
        if column not in df.columns:
            self.logger.warning(f"Column {column} not found for categorical validation")
            return True, 0

        invalid_mask = ~df[column].isin(allowed_values)
        invalid_count = invalid_mask.sum()
        invalid_pct = (invalid_count / len(df)) * 100

        if invalid_count > 0:
            invalid_values = df.loc[invalid_mask, column].unique()
            self.logger.error(
                f"{invalid_count} invalid values in {column} ({invalid_pct:.2f}%): "
                f"{invalid_values}"
            )
            is_valid = False
        else:
            is_valid = True

        self.validation_report.append({
            'check': f'categorical_{column}',
            'is_valid': is_valid,
            'details': {
                'invalid_count': int(invalid_count),
                'invalid_pct': float(invalid_pct),
                'allowed_values': allowed_values
            }
        })

        return is_valid, int(invalid_count)

    def generate_quality_report(self) -> Dict:
        """
        Generate comprehensive data quality report

        Returns:
            Dictionary containing validation results
        """
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_checks': len(self.validation_report),
            'passed_checks': sum(1 for v in self.validation_report if v.get('is_valid', False)),
            'failed_checks': sum(1 for v in self.validation_report if not v.get('is_valid', False)),
            'validations': self.validation_report,
            'overall_status': all(
                v.get('is_valid', False)
                for v in self.validation_report
            )
        }

        self.logger.info(
            f"Quality report: {report['passed_checks']}/{report['total_checks']} checks passed"
        )

        return report

    def validate_all(self, df: pd.DataFrame) -> bool:
        """
        Run all validation checks

        Args:
            df: DataFrame to validate

        Returns:
            True if all validations pass, False otherwise
        """
        self.logger.info("Running comprehensive data quality checks...")

        # Completeness
        required_cols = ['sale_id', 'sale_datetime', 'medication_code', 'sales_quantity']
        completeness_valid, _ = self.validate_completeness(df, required_cols)

        # Duplicates
        duplicates_valid, _ = self.validate_duplicates(df, ['sale_id'])

        # Range checks
        range_valid_sales, _ = self.validate_range(
            df, 'sales_quantity', min_val=0, max_val=10000
        )

        if 'year' in df.columns:
            range_valid_year, _ = self.validate_range(
                df, 'year', min_val=2014, max_val=2025
            )
        else:
            range_valid_year = True

        # Categorical checks
        categorical_valid_med, _ = self.validate_categorical(
            df, 'medication_code',
            ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']
        )

        categorical_valid_gran, _ = self.validate_categorical(
            df, 'granularity',
            ['HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY']
        )

        # Overall validation result
        all_valid = all([
            completeness_valid,
            duplicates_valid,
            range_valid_sales,
            range_valid_year,
            categorical_valid_med,
            categorical_valid_gran
        ])

        if all_valid:
            self.logger.info("All data quality checks passed")
        else:
            self.logger.error("Some data quality checks failed")

        return all_valid
