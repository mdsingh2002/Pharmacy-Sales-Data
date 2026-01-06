-- Fact Table: Sales (all granularities)
-- Contains sales transactions at hourly, daily, weekly, and monthly levels

CREATE TABLE IF NOT EXISTS `project_id.pharmacy_sales.fact_sales_hourly` (
  -- Primary identifiers
  sale_id STRING NOT NULL,
  sale_datetime TIMESTAMP NOT NULL,
  date_key DATE NOT NULL,
  medication_code STRING NOT NULL,
  granularity STRING NOT NULL,

  -- Sales metrics
  sales_quantity FLOAT64,
  total_sales FLOAT64,

  -- Temporal attributes (denormalized for performance)
  year INT64,
  month INT64,
  week_of_year INT64,
  day_of_week INT64,
  hour INT64,
  weekday_name STRING,

  -- Calculated metrics
  running_total FLOAT64,
  moving_avg_7d FLOAT64,
  moving_avg_30d FLOAT64,
  yoy_sales FLOAT64,
  yoy_growth_pct FLOAT64,

  -- Data quality flags
  is_zero_sale BOOL,
  is_outlier BOOL,
  outlier_score FLOAT64,

  -- Metadata
  source_file STRING,
  load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  etl_batch_id STRING
)
PARTITION BY DATE(sale_datetime)
CLUSTER BY medication_code, granularity, year, month
OPTIONS(
  description="Fact table for pharmacy sales at multiple granularities",
  labels=[("environment", "production"), ("domain", "pharmacy")],
  partition_expiration_days=NULL
);

-- Add comments on specific columns
-- Note: BigQuery doesn't support COMMENT ON COLUMN,
-- but descriptions can be added via the schema

-- Sample query to verify partitioning
-- SELECT
--   _PARTITIONTIME as partition_date,
--   COUNT(*) as row_count,
--   SUM(sales_quantity) as total_sales
-- FROM `project_id.pharmacy_sales.fact_sales_hourly`
-- GROUP BY partition_date
-- ORDER BY partition_date;
