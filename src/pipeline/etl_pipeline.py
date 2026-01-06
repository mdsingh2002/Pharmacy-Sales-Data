"""
Main ETL Pipeline Orchestrator
Coordinates Extract, Transform, Load operations
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
import logging

from src.extract.csv_extractor import CSVExtractor
from src.transform.data_cleaner import DataCleaner
from src.transform.data_enricher import DataEnricher
from src.transform.metric_calculator import MetricCalculator
from src.transform.data_validator import DataValidator
from src.load.bigquery_loader import BigQueryLoader
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logging


class PharmacyETLPipeline:
    """Main ETL Pipeline for Pharmacy Sales Data"""

    def __init__(self, config_path: str):
        """
        Initialize pipeline with configuration

        Args:
            config_path: Path to config.yaml
        """
        # Load configuration
        self.config = ConfigLoader(config_path).load()

        # Setup logging
        self.logger = setup_logging(self.config['logging'])

        # Generate unique batch ID
        self.batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.logger.info(f"Initializing ETL pipeline - Batch ID: {self.batch_id}")

        # Initialize components
        self.extractor = CSVExtractor(
            self.config['data']['raw_dir']
        )
        self.cleaner = DataCleaner()
        self.enricher = DataEnricher(
            self.config['medication_mapping']
        )
        self.metric_calculator = MetricCalculator()
        self.validator = DataValidator(
            self.config['data_quality']
        )

        # Initialize BigQuery loader (only if credentials are provided)
        self.loader = None
        if self.config['bigquery'].get('credentials_path'):
            try:
                self.loader = BigQueryLoader(
                    project_id=self.config['bigquery']['project_id'],
                    dataset_id=self.config['bigquery']['dataset_id'],
                    credentials_path=self.config['bigquery']['credentials_path']
                )
                self.logger.info("BigQuery loader initialized")
            except Exception as e:
                self.logger.warning(f"BigQuery loader not initialized: {str(e)}")

        self.logger.info("Pipeline initialization complete")

    def run(self) -> bool:
        """
        Execute full ETL pipeline

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"=== Starting ETL Pipeline - Batch: {self.batch_id} ===")

            # 1. EXTRACT
            self.logger.info("=== EXTRACT PHASE ===")
            raw_data = self.extract_data()

            # 2. TRANSFORM
            self.logger.info("=== TRANSFORM PHASE ===")
            transformed_data = self.transform_data(raw_data)

            # 3. VALIDATE
            self.logger.info("=== VALIDATION PHASE ===")
            is_valid = self.validate_data(transformed_data)

            if not is_valid:
                self.logger.error("Data validation failed. Aborting load.")
                return False

            # 4. LOAD
            if self.loader:
                self.logger.info("=== LOAD PHASE ===")
                self.load_data(transformed_data)
            else:
                self.logger.warning("Skipping load phase (BigQuery loader not initialized)")
                self.logger.info("Transformed data ready for export")

            self.logger.info(f"=== ETL Pipeline Completed Successfully - Batch: {self.batch_id} ===")
            return True

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            return False

    def extract_data(self) -> dict:
        """
        Extract data from all CSV files

        Returns:
            Dictionary of DataFrames by granularity
        """
        self.logger.info("Extracting data from CSV files...")
        return self.extractor.extract_all_sales_files()

    def transform_data(self, raw_data: dict) -> pd.DataFrame:
        """
        Transform all datasets:
        1. Clean data
        2. Unpivot medications
        3. Enrich with descriptions
        4. Calculate metrics
        5. Combine all granularities

        Args:
            raw_data: Dictionary of raw DataFrames

        Returns:
            Combined transformed DataFrame
        """
        medication_cols = ['M01AB', 'M01AE', 'N02BA', 'N02BE',
                          'N05B', 'N05C', 'R03', 'R06']

        all_data = []

        for granularity, df in raw_data.items():
            self.logger.info(f"Transforming {granularity} data ({len(df)} rows)...")

            # Clean
            df = self.cleaner.standardize_datetime(df, granularity)
            df = self.cleaner.handle_missing_values(df, medication_cols)
            df = self.cleaner.validate_data_types(df, medication_cols)
            df = self.cleaner.handle_negative_values(df, medication_cols)

            # Unpivot
            df = self.enricher.unpivot_medications(df)

            # Enrich
            df = self.enricher.add_medication_descriptions(df)
            df = self.enricher.generate_sale_id(df)
            df = self.enricher.add_source_metadata(df, f"{granularity.lower()}.csv")

            # Calculate metrics
            df = self.metric_calculator.calculate_running_total(df)
            df = self.metric_calculator.calculate_moving_averages(df)
            df = self.metric_calculator.calculate_yoy_metrics(df)
            df = self.metric_calculator.flag_zero_sales(df)

            # Detect outliers
            df = self.validator.detect_outliers(df)

            all_data.append(df)

        # Combine all granularities
        combined_df = pd.concat(all_data, ignore_index=True)

        self.logger.info(f"Transformation complete: {len(combined_df)} total records")

        return combined_df

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Run comprehensive data quality checks

        Args:
            df: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        self.logger.info("Running data quality validation...")

        # Run all validations
        is_valid = self.validator.validate_all(df)

        # Generate quality report
        quality_report = self.validator.generate_quality_report()

        self.logger.info(f"Validation complete: {quality_report['passed_checks']}/{quality_report['total_checks']} checks passed")

        return is_valid

    def load_data(self, df: pd.DataFrame) -> None:
        """
        Load data to BigQuery:
        1. Load dimension tables (medications, dates)
        2. Load fact table (sales)

        Args:
            df: Transformed data to load
        """
        if not self.loader:
            raise RuntimeError("BigQuery loader not initialized")

        # Ensure dataset exists
        self.loader.create_dataset_if_not_exists()

        # Load dimension: medications
        self.logger.info("Loading dim_medication...")
        dim_medication = df[[
            'medication_code', 'medication_category',
            'medication_description', 'medication_type'
        ]].drop_duplicates()

        # Add is_active flag
        dim_medication['is_active'] = True

        self.loader.load_dimension_table(
            dim_medication, 'dim_medication'
        )

        # Load dimension: dates
        self.logger.info("Loading dim_date...")
        dim_date = self._create_date_dimension(df)
        self.loader.load_dimension_table(
            dim_date, 'dim_date'
        )

        # Load fact table
        self.logger.info("Loading fact_sales_hourly...")
        fact_cols = [
            'sale_id', 'sale_datetime', 'date_key', 'medication_code',
            'granularity', 'sales_quantity', 'year', 'month', 'hour',
            'weekday_name', 'running_total', 'moving_avg_7d',
            'moving_avg_30d', 'yoy_sales', 'yoy_growth_pct',
            'is_zero_sale', 'is_outlier', 'outlier_score', 'source_file'
        ]

        # Select only existing columns
        available_cols = [col for col in fact_cols if col in df.columns]
        fact_df = df[available_cols].copy()

        self.loader.load_fact_table(
            fact_df, 'fact_sales_hourly', self.batch_id
        )

        self.logger.info("Data load complete")

    def _create_date_dimension(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create date dimension from sales data

        Args:
            df: Sales DataFrame

        Returns:
            Date dimension DataFrame
        """
        dates = pd.DataFrame({
            'date_key': pd.to_datetime(df['date_key'].unique())
        })

        dates['year'] = dates['date_key'].dt.year
        dates['quarter'] = dates['date_key'].dt.quarter
        dates['month'] = dates['date_key'].dt.month
        dates['month_name'] = dates['date_key'].dt.month_name()
        dates['week_of_year'] = dates['date_key'].dt.isocalendar().week.astype(int)
        dates['day_of_month'] = dates['date_key'].dt.day
        dates['day_of_week'] = dates['date_key'].dt.dayofweek
        dates['day_name'] = dates['date_key'].dt.day_name()
        dates['is_weekend'] = dates['day_of_week'].isin([5, 6])
        dates['is_holiday'] = False  # Placeholder
        dates['fiscal_year'] = dates['year']  # Placeholder
        dates['fiscal_quarter'] = dates['quarter']  # Placeholder

        self.logger.info(f"Created date dimension: {len(dates)} dates")

        return dates

    def export_to_csv(self, df: pd.DataFrame, filename: str) -> None:
        """
        Export transformed data to CSV (useful for testing without BigQuery)

        Args:
            df: DataFrame to export
            filename: Output filename
        """
        output_path = Path(self.config['data']['processed_dir']) / filename

        df.to_csv(output_path, index=False)
        self.logger.info(f"Exported data to {output_path}")
