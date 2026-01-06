"""
Setup Script: Create BigQuery Dataset and Tables
Run this once to initialize your BigQuery environment
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.load.bigquery_loader import BigQueryLoader
from src.utils.config_loader import ConfigLoader


def setup_bigquery():
    """Create BigQuery dataset and all tables"""

    print("=" * 60)
    print("BigQuery Setup Script")
    print("=" * 60)

    # Load configuration
    print("\n[1/4] Loading configuration...")
    config_path = project_root / 'config' / 'config.yaml'
    config = ConfigLoader(str(config_path)).load()

    print(f"   ✓ Project ID: {config['bigquery']['project_id']}")
    print(f"   ✓ Dataset ID: {config['bigquery']['dataset_id']}")

    # Initialize BigQuery loader
    print("\n[2/4] Connecting to BigQuery...")
    try:
        loader = BigQueryLoader(
            project_id=config['bigquery']['project_id'],
            dataset_id=config['bigquery']['dataset_id'],
            credentials_path=config['bigquery']['credentials_path']
        )
        print("   ✓ Connected successfully")
    except Exception as e:
        print(f"   ✗ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check that config/gcp-credentials.json exists")
        print("  2. Verify project_id in config/config.yaml is correct")
        print("  3. Ensure BigQuery API is enabled in GCP Console")
        return False

    # Create dataset
    print("\n[3/4] Creating BigQuery dataset...")
    try:
        loader.create_dataset_if_not_exists()
        print(f"   ✓ Dataset '{config['bigquery']['dataset_id']}' is ready")
    except Exception as e:
        print(f"   ✗ Failed to create dataset: {str(e)}")
        return False

    # Create tables from DDL files
    print("\n[4/4] Creating tables...")

    ddl_files = [
        ('dim_medication', 'sql/ddl/create_dim_medication.sql'),
        ('dim_date', 'sql/ddl/create_dim_date.sql'),
        ('fact_sales_hourly', 'sql/ddl/create_fact_sales.sql'),
        ('view_unified_sales', 'sql/ddl/create_view_unified_sales.sql')
    ]

    for table_name, ddl_path in ddl_files:
        try:
            full_path = project_root / ddl_path

            # Read DDL file
            with open(full_path, 'r') as f:
                ddl = f.read()

            # Replace project_id placeholder
            ddl = ddl.replace('project_id', config['bigquery']['project_id'])

            # Execute DDL
            loader.client.query(ddl).result()
            print(f"   ✓ Created: {table_name}")

        except Exception as e:
            # Table might already exist, which is fine
            if 'already exists' in str(e).lower():
                print(f"   ✓ Already exists: {table_name}")
            else:
                print(f"   ✗ Failed to create {table_name}: {str(e)}")

    # Success summary
    print("\n" + "=" * 60)
    print("✅ BigQuery Setup Complete!")
    print("=" * 60)
    print(f"\nView your dataset:")
    print(f"https://console.cloud.google.com/bigquery?project={config['bigquery']['project_id']}&d={config['bigquery']['dataset_id']}")
    print("\nNext steps:")
    print("  1. Run the ETL pipeline: python scripts/run_pipeline.py")
    print("  2. View data in BigQuery console")
    print("  3. Connect Tableau to your BigQuery dataset")

    return True


if __name__ == '__main__':
    success = setup_bigquery()
    sys.exit(0 if success else 1)
