"""
Data Enrichment Module
Unpivots medication columns and adds descriptive information
"""

import pandas as pd
from typing import Dict
import logging


class DataEnricher:
    """Enrich sales data with medication descriptions"""

    def __init__(self, medication_mapping: Dict[str, Dict[str, str]]):
        """
        Initialize data enricher

        Args:
            medication_mapping: Dictionary mapping codes to descriptions
        """
        self.medication_mapping = medication_mapping
        self.logger = logging.getLogger(__name__)

    def unpivot_medications(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform wide format to long format (unpivot medication columns)

        Before: | datum | M01AB | M01AE | N02BA | ...
        After:  | datum | medication_code | sales_quantity |

        Args:
            df: Input DataFrame in wide format

        Returns:
            DataFrame in long format
        """
        medication_cols = ['M01AB', 'M01AE', 'N02BA', 'N02BE',
                          'N05B', 'N05C', 'R03', 'R06']

        # Identify ID columns (everything except medication sales)
        id_cols = [col for col in df.columns if col not in medication_cols]

        # Melt/unpivot
        df_long = df.melt(
            id_vars=id_cols,
            value_vars=medication_cols,
            var_name='medication_code',
            value_name='sales_quantity'
        )

        self.logger.info(
            f"Unpivoted {len(df)} rows to {len(df_long)} rows "
            f"({len(medication_cols)} medications)"
        )

        return df_long

    def add_medication_descriptions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add medication category, type, and description

        Args:
            df: Input DataFrame with medication_code column

        Returns:
            DataFrame with medication descriptions added
        """
        df = df.copy()

        # Create mapping DataFrame
        med_df = pd.DataFrame([
            {
                'medication_code': code,
                'medication_category': info.get('category', ''),
                'medication_description': info.get('description', ''),
                'medication_type': info.get('type', '')
            }
            for code, info in self.medication_mapping.items()
        ])

        # Merge with sales data
        df = df.merge(med_df, on='medication_code', how='left')

        # Log any unmapped codes
        unmapped = df[df['medication_description'].isna()]['medication_code'].unique()
        if len(unmapped) > 0:
            self.logger.warning(f"Found unmapped medication codes: {unmapped}")

        self.logger.info("Added medication descriptions")

        return df

    def generate_sale_id(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate unique sale_id for each record
        Format: {granularity}_{datetime}_{medication_code}

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with sale_id column added
        """
        df = df.copy()

        # Generate sale_id
        df['sale_id'] = (
            df['granularity'] + '_' +
            df['sale_datetime'].astype(str).str.replace(' ', 'T') + '_' +
            df['medication_code']
        )

        self.logger.info(f"Generated {len(df)} unique sale IDs")

        # Verify uniqueness
        if df['sale_id'].duplicated().any():
            dup_count = df['sale_id'].duplicated().sum()
            self.logger.error(f"Found {dup_count} duplicate sale IDs!")

        return df

    def add_source_metadata(self, df: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """
        Add metadata about source file

        Args:
            df: Input DataFrame
            source_file: Name of source CSV file

        Returns:
            DataFrame with source metadata
        """
        df = df.copy()
        df['source_file'] = source_file

        return df

    def calculate_total_sales_per_record(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate total sales across all medications for each timestamp
        (This is done per medication after unpivot, so we just copy sales_quantity)

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with total_sales column
        """
        df = df.copy()

        # After unpivot, each row represents one medication
        # So total_sales per row is just the sales_quantity
        df['total_sales'] = df['sales_quantity']

        return df
