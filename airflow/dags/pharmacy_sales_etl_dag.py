"""
Airflow DAG for Pharmacy Sales ETL Pipeline
Runs daily to process pharmacy sales data
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.etl_pipeline import PharmacyETLPipeline

# Default arguments
default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email': [Variable.get('alert_email', default_var='admin@pharmacy.com')],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2)
}

# DAG definition
dag = DAG(
    'pharmacy_sales_etl',
    default_args=default_args,
    description='ETL pipeline for pharmacy sales data to BigQuery',
    schedule_interval='0 2 * * *',  # Run daily at 2 AM
    start_date=days_ago(1),
    catchup=False,
    tags=['pharmacy', 'sales', 'bigquery', 'etl']
)


def run_full_pipeline(**context):
    """
    Run the complete ETL pipeline

    Args:
        **context: Airflow context with execution metadata
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting Pharmacy Sales ETL Pipeline...")

    # Initialize pipeline
    config_path = str(project_root / 'config' / 'config.yaml')
    pipeline = PharmacyETLPipeline(config_path)

    # Run pipeline
    success = pipeline.run()

    if not success:
        raise ValueError("ETL pipeline failed!")

    # Push metrics to XCom
    context['task_instance'].xcom_push(key='batch_id', value=pipeline.batch_id)
    context['task_instance'].xcom_push(key='status', value='SUCCESS')

    logger.info("Pipeline completed successfully")

    return success


def run_extract_task(**context):
    """Extract task: Read CSV files"""
    logger = logging.getLogger(__name__)
    logger.info("Starting data extraction...")

    config_path = str(project_root / 'config' / 'config.yaml')
    pipeline = PharmacyETLPipeline(config_path)

    raw_data = pipeline.extract_data()

    # Push metrics to XCom
    total_records = sum(len(df) for df in raw_data.values())
    context['task_instance'].xcom_push(key='extract_count', value=total_records)

    logger.info(f"Extracted {total_records} total records")

    return total_records


def run_transform_task(**context):
    """Transform task: Clean, enrich, calculate metrics"""
    logger = logging.getLogger(__name__)
    logger.info("Starting data transformation...")

    config_path = str(project_root / 'config' / 'config.yaml')
    pipeline = PharmacyETLPipeline(config_path)

    # Extract
    raw_data = pipeline.extract_data()

    # Transform
    transformed_data = pipeline.transform_data(raw_data)

    # Export to CSV for inspection (optional)
    pipeline.export_to_csv(transformed_data, 'transformed_sales.csv')

    # Push metrics to XCom
    context['task_instance'].xcom_push(key='transform_count', value=len(transformed_data))

    logger.info(f"Transformed {len(transformed_data)} records")

    return len(transformed_data)


def run_validate_task(**context):
    """Validate task: Data quality checks"""
    logger = logging.getLogger(__name__)
    logger.info("Starting data validation...")

    config_path = str(project_root / 'config' / 'config.yaml')
    pipeline = PharmacyETLPipeline(config_path)

    # Extract & Transform
    raw_data = pipeline.extract_data()
    transformed_data = pipeline.transform_data(raw_data)

    # Validate
    is_valid = pipeline.validate_data(transformed_data)

    # Push validation report to XCom
    quality_report = pipeline.validator.generate_quality_report()
    context['task_instance'].xcom_push(key='quality_report', value=quality_report)

    if not is_valid:
        raise ValueError("Data quality validation failed!")

    logger.info("Data validation passed")

    return is_valid


def run_load_task(**context):
    """Load task: Load to BigQuery"""
    logger = logging.getLogger(__name__)
    logger.info("Starting data load to BigQuery...")

    config_path = str(project_root / 'config' / 'config.yaml')
    pipeline = PharmacyETLPipeline(config_path)

    # Run full pipeline (includes load)
    success = pipeline.run()

    if not success:
        raise ValueError("ETL pipeline load failed!")

    # Push batch ID to XCom
    context['task_instance'].xcom_push(key='batch_id', value=pipeline.batch_id)

    logger.info(f"Data loaded successfully to BigQuery (batch: {pipeline.batch_id})")

    return success


def send_success_notification(**context):
    """Send success notification with metrics"""
    batch_id = context['task_instance'].xcom_pull(
        task_ids='run_full_etl', key='batch_id'
    )

    message = f"""
    Pharmacy Sales ETL Pipeline Completed Successfully

    Execution Date: {context['execution_date']}
    DAG Run ID: {context['run_id']}
    Batch ID: {batch_id}

    Data loaded to BigQuery successfully.

    Dashboard: https://console.cloud.google.com/bigquery
    """

    logging.info(message)

    return message


# Define tasks

# Option 1: Single task that runs entire pipeline
run_full_etl = PythonOperator(
    task_id='run_full_etl',
    python_callable=run_full_pipeline,
    provide_context=True,
    dag=dag
)

success_notification = PythonOperator(
    task_id='send_success_notification',
    python_callable=send_success_notification,
    provide_context=True,
    dag=dag
)

# Define task dependencies
run_full_etl >> success_notification


# Option 2: Separate tasks for each phase (commented out)
# Uncomment to use granular task separation

# extract_task = PythonOperator(
#     task_id='extract_data',
#     python_callable=run_extract_task,
#     provide_context=True,
#     dag=dag
# )
#
# transform_task = PythonOperator(
#     task_id='transform_data',
#     python_callable=run_transform_task,
#     provide_context=True,
#     dag=dag
# )
#
# validate_task = PythonOperator(
#     task_id='validate_data',
#     python_callable=run_validate_task,
#     provide_context=True,
#     dag=dag
# )
#
# load_task = PythonOperator(
#     task_id='load_to_bigquery',
#     python_callable=run_load_task,
#     provide_context=True,
#     dag=dag
# )
#
# # Task dependencies
# extract_task >> transform_task >> validate_task >> load_task >> success_notification
