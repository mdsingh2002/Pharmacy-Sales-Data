-- Dimension Table: Date
-- Contains date attributes for time-based analysis

CREATE TABLE IF NOT EXISTS `project_id.pharmacy_sales.dim_date` (
  date_key DATE NOT NULL,
  year INT64,
  quarter INT64,
  month INT64,
  month_name STRING,
  week_of_year INT64,
  day_of_month INT64,
  day_of_week INT64,
  day_name STRING,
  is_weekend BOOL,
  is_holiday BOOL,
  fiscal_year INT64,
  fiscal_quarter INT64
)
PARTITION BY date_key
OPTIONS(
  description="Date dimension table for time-based analysis",
  labels=[("environment", "production"), ("domain", "pharmacy")],
  partition_expiration_days=NULL
);

-- Create index on commonly queried columns
-- BigQuery automatically optimizes queries, but clustering helps
-- ALTER TABLE `project_id.pharmacy_sales.dim_date`
-- CLUSTER BY year, month;
