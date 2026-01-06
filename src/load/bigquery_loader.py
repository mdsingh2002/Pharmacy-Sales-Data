"""
BigQuery Loader Module
Handles loading data to BigQuery with error handling
"""

import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from typing import Optional
import logging
import time


class BigQueryLoader:
    """Load data to BigQuery tables"""

    def __init__(self, project_id: str, dataset_id: str,
                 credentials_path: Optional[str] = None):
        """
        Initialize BigQuery client

        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            credentials_path: Path to service account JSON (optional)
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.logger = logging.getLogger(__name__)

        try:
            if credentials_path:
                self.client = bigquery.Client.from_service_account_json(
                    credentials_path,
                    project=project_id
                )
                self.logger.info(f"BigQuery client initialized with credentials from {credentials_path}")
            else:
                self.client = bigquery.Client(project=project_id)
                self.logger.info("BigQuery client initialized with default credentials")

        except Exception as e:
            self.logger.error(f"Failed to initialize BigQuery client: {str(e)}")
            raise

    def create_dataset_if_not_exists(self) -> None:
        """Create dataset if it doesn't exist"""
        dataset_ref = f"{self.project_id}.{self.dataset_id}"

        try:
            self.client.get_dataset(dataset_ref)
            self.logger.info(f"Dataset {dataset_ref} already exists")

        except GoogleCloudError:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            self.client.create_dataset(dataset, timeout=30)
            self.logger.info(f"Created dataset {dataset_ref}")

    def load_dataframe(self, df: pd.DataFrame, table_name: str,
                      write_disposition: str = 'WRITE_APPEND') -> None:
        """
        Load pandas DataFrame to BigQuery table

        Args:
            df: DataFrame to load
            table_name: Target table name
            write_disposition: WRITE_APPEND, WRITE_TRUNCATE, or WRITE_EMPTY

        Raises:
            GoogleCloudError: If load fails
        """
        table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"

        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            create_disposition='CREATE_IF_NEEDED'
        )

        try:
            self.logger.info(f"Starting load to {table_ref}: {len(df)} rows")
            start_time = time.time()

            job = self.client.load_table_from_dataframe(
                df, table_ref, job_config=job_config
            )
            job.result()  # Wait for completion

            duration = time.time() - start_time
            self.logger.info(
                f"Successfully loaded {len(df)} rows to {table_ref} "
                f"in {duration:.2f} seconds"
            )

        except GoogleCloudError as e:
            self.logger.error(f"Failed to load data to {table_ref}: {str(e)}")
            raise

    def execute_sql(self, sql: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame

        Args:
            sql: SQL query to execute

        Returns:
            Query results as DataFrame

        Raises:
            GoogleCloudError: If query fails
        """
        try:
            self.logger.info("Executing SQL query...")
            query_job = self.client.query(sql)
            result = query_job.to_dataframe()

            self.logger.info(f"Query returned {len(result)} rows")
            return result

        except GoogleCloudError as e:
            self.logger.error(f"Query failed: {str(e)}")
            raise

    def load_dimension_table(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Load dimension table (truncate and reload)

        Args:
            df: DataFrame to load
            table_name: Target table name
        """
        self.logger.info(f"Loading dimension table: {table_name}")

        self.load_dataframe(
            df, table_name,
            write_disposition='WRITE_TRUNCATE'
        )

    def load_fact_table(self, df: pd.DataFrame,
                       table_name: str,
                       etl_batch_id: str) -> None:
        """
        Load fact table with batch tracking

        Args:
            df: DataFrame to load
            table_name: Target table name
            etl_batch_id: Unique batch identifier
        """
        df = df.copy()
        df['etl_batch_id'] = etl_batch_id
        df['load_timestamp'] = pd.Timestamp.now()

        self.logger.info(f"Loading fact table: {table_name} (batch: {etl_batch_id})")

        self.load_dataframe(
            df, table_name,
            write_disposition='WRITE_APPEND'
        )

    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists

        Args:
            table_name: Table name to check

        Returns:
            True if table exists, False otherwise
        """
        table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"

        try:
            self.client.get_table(table_ref)
            return True
        except GoogleCloudError:
            return False

    def get_row_count(self, table_name: str) -> int:
        """
        Get row count of a table

        Args:
            table_name: Table name

        Returns:
            Number of rows in table
        """
        sql = f"""
        SELECT COUNT(*) as row_count
        FROM `{self.project_id}.{self.dataset_id}.{table_name}`
        """

        try:
            result = self.execute_sql(sql)
            return int(result['row_count'].iloc[0])

        except Exception as e:
            self.logger.error(f"Failed to get row count: {str(e)}")
            return 0

    def delete_batch(self, table_name: str, batch_id: str) -> None:
        """
        Delete records for a specific batch

        Args:
            table_name: Table name
            batch_id: Batch ID to delete
        """
        sql = f"""
        DELETE FROM `{self.project_id}.{self.dataset_id}.{table_name}`
        WHERE etl_batch_id = '{batch_id}'
        """

        try:
            self.logger.info(f"Deleting batch {batch_id} from {table_name}")
            query_job = self.client.query(sql)
            query_job.result()
            self.logger.info(f"Successfully deleted batch {batch_id}")

        except GoogleCloudError as e:
            self.logger.error(f"Failed to delete batch: {str(e)}")
            raise

    def create_table_from_ddl(self, ddl_file_path: str) -> None:
        """
        Create table from DDL SQL file

        Args:
            ddl_file_path: Path to SQL file containing CREATE TABLE statement
        """
        with open(ddl_file_path, 'r') as f:
            ddl = f.read()

        # Replace placeholder with actual project_id
        ddl = ddl.replace('project_id', self.project_id)

        try:
            self.logger.info(f"Executing DDL from {ddl_file_path}")
            query_job = self.client.query(ddl)
            query_job.result()
            self.logger.info("DDL executed successfully")

        except GoogleCloudError as e:
            self.logger.error(f"Failed to execute DDL: {str(e)}")
            raise
