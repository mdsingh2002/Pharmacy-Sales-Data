"""
Cleanup Script: Delete BigQuery Dataset
Run this when you're done with the project to avoid any charges
"""

from google.cloud import bigquery
from src.utils.config_loader import ConfigLoader

def cleanup_bigquery():
    """Delete the entire BigQuery dataset and all tables"""

    # Load config
    config = ConfigLoader('config/config.yaml').load()

    # Initialize client
    client = bigquery.Client.from_service_account_json(
        config['bigquery']['credentials_path'],
        project=config['bigquery']['project_id']
    )

    dataset_id = f"{config['bigquery']['project_id']}.{config['bigquery']['dataset_id']}"

    # Confirm deletion
    print(f"\n⚠️  WARNING: This will delete dataset: {dataset_id}")
    print("This includes ALL tables and data.")
    confirm = input("Type 'DELETE' to confirm: ")

    if confirm != 'DELETE':
        print("❌ Cancelled. No data deleted.")
        return

    # Delete dataset (delete_contents=True removes all tables)
    client.delete_dataset(dataset_id, delete_contents=True, not_found_ok=True)

    print(f"✅ Successfully deleted dataset: {dataset_id}")
    print(f"💰 You will no longer be charged for BigQuery storage.")
    print(f"\nTo delete the entire GCP project:")
    print(f"   https://console.cloud.google.com/iam-admin/settings?project={config['bigquery']['project_id']}")

if __name__ == '__main__':
    cleanup_bigquery()
