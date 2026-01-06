"""
Run Script: Execute the ETL Pipeline
This is the main script to run the pharmacy sales ETL pipeline
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.etl_pipeline import PharmacyETLPipeline


def run_pipeline():
    """Execute the complete ETL pipeline"""

    print("=" * 60)
    print("Pharmacy Sales ETL Pipeline")
    print("=" * 60)

    # Initialize pipeline
    config_path = project_root / 'config' / 'config.yaml'

    try:
        print("\nInitializing pipeline...")
        pipeline = PharmacyETLPipeline(str(config_path))

        print(f"Batch ID: {pipeline.batch_id}\n")

        # Run pipeline
        success = pipeline.run()

        # Summary
        print("\n" + "=" * 60)
        if success:
            print("✅ Pipeline completed successfully!")
            print("=" * 60)
            print(f"\nBatch ID: {pipeline.batch_id}")
            print("\nNext steps:")
            print("  1. View data in BigQuery console")
            print("  2. Check logs: logs/etl_pipeline.log")
            print("  3. Connect Tableau to BigQuery")
            return True
        else:
            print("❌ Pipeline failed!")
            print("=" * 60)
            print("\nCheck logs for details: logs/etl_pipeline.log")
            return False

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Ensure BigQuery is set up: python scripts/setup_bigquery.py")
        print("  2. Check CSV files exist in data/ directory")
        print("  3. Verify config/config.yaml has correct project_id")
        print("  4. Review logs: logs/etl_pipeline.log")
        return False


if __name__ == '__main__':
    success = run_pipeline()
    sys.exit(0 if success else 1)
