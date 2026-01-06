-- View: Unified Sales
-- Pre-joined view combining fact and dimension tables for Tableau

CREATE OR REPLACE VIEW `project_id.pharmacy_sales.view_unified_sales` AS
SELECT
  -- Identifiers
  fs.sale_id,
  fs.sale_datetime,
  fs.granularity,

  -- Medication dimension
  dm.medication_code,
  dm.medication_category,
  dm.medication_description,
  dm.medication_type,
  dm.atc_level_1,
  dm.atc_level_2,

  -- Date dimension
  dd.year,
  dd.quarter,
  dd.month,
  dd.month_name,
  dd.week_of_year,
  dd.day_of_month,
  dd.day_of_week,
  dd.day_name,
  dd.is_weekend,
  dd.is_holiday,

  -- Time attributes
  fs.hour,
  fs.weekday_name,

  -- Sales metrics
  fs.sales_quantity,
  fs.total_sales,
  fs.running_total,
  fs.moving_avg_7d,
  fs.moving_avg_30d,
  fs.yoy_sales,
  fs.yoy_growth_pct,

  -- Quality flags
  fs.is_zero_sale,
  fs.is_outlier,
  fs.outlier_score,

  -- Metadata
  fs.source_file,
  fs.etl_batch_id,
  fs.load_timestamp

FROM
  `project_id.pharmacy_sales.fact_sales_hourly` fs

LEFT JOIN
  `project_id.pharmacy_sales.dim_medication` dm
  ON fs.medication_code = dm.medication_code

LEFT JOIN
  `project_id.pharmacy_sales.dim_date` dd
  ON fs.date_key = dd.date_key;

-- Sample queries for Tableau dashboards

-- 1. Total sales by medication category
-- SELECT
--   medication_category,
--   SUM(sales_quantity) as total_sales,
--   COUNT(*) as transaction_count
-- FROM `project_id.pharmacy_sales.view_unified_sales`
-- GROUP BY medication_category
-- ORDER BY total_sales DESC;

-- 2. Monthly sales trend
-- SELECT
--   year,
--   month,
--   month_name,
--   SUM(sales_quantity) as monthly_sales
-- FROM `project_id.pharmacy_sales.view_unified_sales`
-- WHERE granularity = 'MONTHLY'
-- GROUP BY year, month, month_name
-- ORDER BY year, month;

-- 3. Top medications by sales
-- SELECT
--   medication_code,
--   medication_description,
--   SUM(sales_quantity) as total_sales,
--   AVG(yoy_growth_pct) as avg_yoy_growth
-- FROM `project_id.pharmacy_sales.view_unified_sales`
-- WHERE yoy_growth_pct IS NOT NULL
-- GROUP BY medication_code, medication_description
-- ORDER BY total_sales DESC
-- LIMIT 10;

-- 4. Hourly sales pattern
-- SELECT
--   hour,
--   AVG(sales_quantity) as avg_sales,
--   SUM(sales_quantity) as total_sales
-- FROM `project_id.pharmacy_sales.view_unified_sales`
-- WHERE granularity = 'HOURLY'
--   AND hour IS NOT NULL
-- GROUP BY hour
-- ORDER BY hour;
