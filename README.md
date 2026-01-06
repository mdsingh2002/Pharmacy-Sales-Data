# Pharmacy Sales ETL Pipeline

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![BigQuery](https://img.shields.io/badge/Google%20BigQuery-Data%20Warehouse-blue.svg)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-Orchestration-red.svg)
![Power BI](https://img.shields.io/badge/Power%20BI-Visualization-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)

A production-ready ETL pipeline to extract pharmacy sales data from CSV files, transform with data quality checks and metric calculations, and load into **Google BigQuery** for Power BI visualization.

**Tech Stack:** Python | BigQuery | Apache Airflow | Pandas | Google Cloud Platform

## Overview

This pipeline processes **50K+ pharmacy sales records** spanning 2014-2019 across 8 medication categories at multiple time granularities (hourly, daily, weekly, monthly).

### Key Features

- **Extract**: Read 4 CSV files with validation
- **Transform**: Clean, unpivot, enrich with medication descriptions, calculate metrics
- **Load**: Star schema in BigQuery (optimized for analytics)
- **Data Quality**: Comprehensive validation with pipeline-stopping checks
- **Orchestration**: Apache Airflow for scheduling and monitoring
- **Visualization**: Pre-built Power BI dashboard integration

## Architecture

### Star Schema in BigQuery

```
fact_sales_hourly (partitioned by date, clustered by medication/granularity)
  ├── dim_medication (8 medications with ATC classifications)
  └── dim_date (date dimension with temporal attributes)

view_unified_sales (pre-joined view for Power BI)
```

### Data Flow

```
CSV Files → Extract → Clean → Unpivot → Enrich → Calculate Metrics → Validate → Load to BigQuery → Power BI
```

## Project Structure

```
Pharmacy-Sales-Data/
├── config/                     # Configuration files
│   ├── config.yaml            # Main configuration
│   ├── medication_mapping.yaml # Medication code mappings
│   └── data_quality_rules.yaml # Validation rules
├── src/                        # Source code
│   ├── extract/               # CSV extraction
│   ├── transform/             # Data transformation
│   ├── load/                  # BigQuery loading
│   ├── utils/                 # Utilities (logging, config)
│   └── pipeline/              # Main ETL orchestrator
├── airflow/                    # Airflow DAGs
├── sql/                        # BigQuery DDL scripts
├── tests/                      # Unit and integration tests
├── data/                       # Data files
│   ├── salesdaily.csv
│   ├── saleshourly.csv
│   ├── salesmonthly.csv
│   └── salesweekly.csv
└── requirements.txt            # Python dependencies
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Google Cloud Platform account
- BigQuery API enabled
- (Optional) Apache Airflow for scheduling

### 1. Environment Setup

```bash
# Clone repository
cd Pharmacy-Sales-Data

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Google Cloud Platform Setup

#### Create GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable BigQuery API

#### Create Service Account

1. Navigate to **IAM & Admin** → **Service Accounts**
2. Create service account: `pharmacy-etl-sa`
3. Grant roles:
   - `BigQuery Data Editor`
   - `BigQuery Job User`
   - `BigQuery Read Session User`
4. Create JSON key and download
5. Save to `config/gcp-credentials.json`

**IMPORTANT**: The credentials file is gitignored. Never commit it to version control.

#### Update Configuration

Edit `config/config.yaml`:

```yaml
bigquery:
  project_id: "your-gcp-project-id" # Replace with your project ID
  dataset_id: "pharmacy_sales"
  credentials_path: "config/gcp-credentials.json"
  location: "US"
```

### 3. Create BigQuery Tables

Run the DDL scripts to create tables:

```bash
# Option 1: Using Python
python -c "from src.load.bigquery_loader import BigQueryLoader; \
           from src.utils.config_loader import ConfigLoader; \
           config = ConfigLoader('config/config.yaml').load(); \
           loader = BigQueryLoader(**config['bigquery']); \
           loader.create_dataset_if_not_exists()"

# Option 2: Using bq command-line tool
bq mk --dataset your-project-id:pharmacy_sales

# Create tables (replace project_id in SQL files first)
bq query < sql/ddl/create_dim_medication.sql
bq query < sql/ddl/create_dim_date.sql
bq query < sql/ddl/create_fact_sales.sql
bq query < sql/ddl/create_view_unified_sales.sql
```

### 4. Run ETL Pipeline

#### Option A: Standalone Execution (Testing)

```bash
python -c "from src.pipeline.etl_pipeline import PharmacyETLPipeline; \
           pipeline = PharmacyETLPipeline('config/config.yaml'); \
           success = pipeline.run(); \
           print('Pipeline succeeded!' if success else 'Pipeline failed!')"
```

#### Option B: Airflow Execution (Production)

```bash
# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@pharmacy.com

# Set Airflow variables
airflow variables set alert_email "your-email@domain.com"

# Start Airflow webserver (Terminal 1)
airflow webserver --port 8080

# Start Airflow scheduler (Terminal 2)
airflow scheduler

# Trigger DAG manually
airflow dags trigger pharmacy_sales_etl

# Access Airflow UI: http://localhost:8080
```

## Configuration

### Medication Codes

The pipeline processes 8 medication categories:

| Code  | Description                                         |
| ----- | --------------------------------------------------- |
| M01AB | Anti-inflammatory, Acetic acid derivatives          |
| M01AE | Anti-inflammatory, Propionic acid derivatives       |
| N02BA | Analgesics/antipyretics, Salicylic acid derivatives |
| N02BE | Analgesics/antipyretics, Pyrazolones and Anilides   |
| N05B  | Psycholeptics, Anxiolytic drugs                     |
| N05C  | Psycholeptics, Hypnotics and sedatives              |
| R03   | Obstructive airway disease drugs                    |
| R06   | Antihistamines for systemic use                     |

### Data Quality Thresholds

| Check                               | Threshold | Action on Fail |
| ----------------------------------- | --------- | -------------- |
| Missing sale_id/datetime/medication | 0%        | FAIL pipeline  |
| Missing sales_quantity              | < 0.5%    | WARN, continue |
| Duplicate sale_id                   | 0%        | FAIL pipeline  |
| Sales quantity range                | 0-10,000  | Flag outliers  |
| Invalid medication code             | 0%        | FAIL pipeline  |

## Data Transformations

### Unpivot (Wide → Long Format)

**Before:**
| datum | M01AB | M01AE | N02BA | ... |
|-------|-------|-------|-------|-----|
| 2014-01 | 127.69 | 99.09 | 152.1 | ... |

**After:**
| datum | medication_code | sales_quantity | medication_description |
|-------|----------------|----------------|----------------------|
| 2014-01 | M01AB | 127.69 | Anti-inflammatory, Acetic acid derivatives |
| 2014-01 | M01AE | 99.09 | Anti-inflammatory, Propionic acid derivatives |

### Calculated Metrics

- **Running Total**: Cumulative sum per medication
- **Moving Averages**: 7-day and 30-day rolling windows
- **YoY Growth**: Year-over-year sales comparison
- **Outlier Detection**: IQR method with z-scores

### Key Measures (DAX)

Create these measures in Power BI (Right-click table → New Measure):

```DAX
Total Sales = SUM('view_unified_sales'[sales_quantity])

Average Sales = AVERAGE('view_unified_sales'[sales_quantity])

YoY Growth % =
DIVIDE(
    SUM('view_unified_sales'[sales_quantity]) - SUM('view_unified_sales'[yoy_sales]),
    SUM('view_unified_sales'[yoy_sales])
) * 100

Weekend Sales =
CALCULATE(
    SUM('view_unified_sales'[sales_quantity]),
    'view_unified_sales'[is_weekend] = TRUE
)

Top Medication =
FIRSTNONBLANK(
    TOPN(1, VALUES('view_unified_sales'[medication_description]), [Total Sales], DESC),
    1
)
```

## Testing

Run unit and integration tests:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Logs

- Application logs: `logs/etl_pipeline.log`
- Airflow logs: `airflow/logs/`
