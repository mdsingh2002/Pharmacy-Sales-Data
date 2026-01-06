"""
Metric Calculation Module
Calculates derived metrics: running totals, YoY, moving averages, etc.
"""

import pandas as pd
import numpy as np
import logging


class MetricCalculator:
    """Calculate advanced metrics for sales data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_running_total(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate running total for each medication over time

        Args:
            df: Input DataFrame with sales_quantity

        Returns:
            DataFrame with running_total column
        """
        df = df.copy()
        df = df.sort_values(['medication_code', 'sale_datetime'])

        df['running_total'] = df.groupby(
            'medication_code'
        )['sales_quantity'].cumsum()

        self.logger.info("Calculated running totals")

        return df

    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate 7-day and 30-day moving averages
        Only applicable for daily/hourly granularity

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with moving average columns
        """
        df = df.copy()
        df = df.sort_values(['medication_code', 'sale_datetime'])

        # 7-day MA
        df['moving_avg_7d'] = df.groupby(
            'medication_code'
        )['sales_quantity'].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )

        # 30-day MA
        df['moving_avg_30d'] = df.groupby(
            'medication_code'
        )['sales_quantity'].transform(
            lambda x: x.rolling(window=30, min_periods=1).mean()
        )

        self.logger.info("Calculated moving averages (7-day and 30-day)")

        return df

    def calculate_yoy_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate year-over-year sales and growth percentage

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with YoY metrics
        """
        df = df.copy()
        df = df.sort_values(['medication_code', 'sale_datetime'])

        # Create a lag of approximately 1 year (365 days)
        df['yoy_sales'] = df.groupby(
            'medication_code'
        )['sales_quantity'].shift(365)

        # Calculate YoY growth percentage
        df['yoy_growth_pct'] = (
            (df['sales_quantity'] - df['yoy_sales']) /
            df['yoy_sales'] * 100
        ).replace([np.inf, -np.inf], np.nan)

        # Count how many YoY comparisons were possible
        yoy_count = df['yoy_sales'].notna().sum()
        self.logger.info(
            f"Calculated YoY metrics ({yoy_count} comparisons available)"
        )

        return df

    def flag_zero_sales(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flag records with zero sales

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with is_zero_sale column
        """
        df = df.copy()
        df['is_zero_sale'] = df['sales_quantity'] == 0

        zero_count = df['is_zero_sale'].sum()
        zero_pct = (zero_count / len(df)) * 100

        self.logger.info(
            f"Flagged {zero_count} zero-sale records ({zero_pct:.2f}%)"
        )

        return df

    def calculate_sales_velocity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate rate of change in sales (velocity)

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with sales_velocity column
        """
        df = df.copy()
        df = df.sort_values(['medication_code', 'sale_datetime'])

        # Calculate difference from previous period
        df['sales_velocity'] = df.groupby(
            'medication_code'
        )['sales_quantity'].diff()

        return df

    def calculate_percentile_rank(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate percentile rank for each sale within its medication

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with sales_percentile column
        """
        df = df.copy()

        df['sales_percentile'] = df.groupby(
            'medication_code'
        )['sales_quantity'].rank(pct=True) * 100

        return df

    def aggregate_by_period(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        Aggregate sales by time period (day, week, month)

        Args:
            df: Input DataFrame
            period: Aggregation period ('D', 'W', 'M')

        Returns:
            Aggregated DataFrame
        """
        df = df.copy()

        # Group by medication and period
        df['period'] = df['sale_datetime'].dt.to_period(period)

        agg_df = df.groupby(['medication_code', 'period']).agg({
            'sales_quantity': ['sum', 'mean', 'std', 'min', 'max', 'count']
        }).reset_index()

        agg_df.columns = ['medication_code', 'period', 'total_sales',
                         'avg_sales', 'std_sales', 'min_sales',
                         'max_sales', 'sale_count']

        self.logger.info(
            f"Aggregated data by {period} period: {len(agg_df)} records"
        )

        return agg_df
