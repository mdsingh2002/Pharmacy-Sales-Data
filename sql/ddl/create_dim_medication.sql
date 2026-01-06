-- Dimension Table: Medication
-- Contains medication codes with full descriptions and ATC classifications

CREATE TABLE IF NOT EXISTS `project_id.pharmacy_sales.dim_medication` (
  medication_code STRING NOT NULL,
  medication_category STRING NOT NULL,
  medication_description STRING NOT NULL,
  medication_type STRING NOT NULL,
  atc_level_1 STRING,
  atc_level_2 STRING,
  is_active BOOL DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
OPTIONS(
  description="Medication dimension table with ATC classification",
  labels=[("environment", "production"), ("domain", "pharmacy")]
);

-- Sample data insert (run after table creation)
-- DELETE FROM `project_id.pharmacy_sales.dim_medication` WHERE 1=1;

-- INSERT INTO `project_id.pharmacy_sales.dim_medication`
-- (medication_code, medication_category, medication_description, medication_type, atc_level_1, atc_level_2)
-- VALUES
--   ('M01AB', 'Anti-inflammatory and antirheumatic products', 'Acetic acid derivatives and related substances', 'Non-steroids', 'M', 'M01'),
--   ('M01AE', 'Anti-inflammatory and antirheumatic products', 'Propionic acid derivatives', 'Non-steroids', 'M', 'M01'),
--   ('N02BA', 'Other analgesics and antipyretics', 'Salicylic acid and derivatives', 'Pain relievers', 'N', 'N02'),
--   ('N02BE', 'Other analgesics and antipyretics', 'Pyrazolones and Anilides', 'Pain relievers', 'N', 'N02'),
--   ('N05B', 'Psycholeptics drugs', 'Anxiolytic drugs', 'Psychiatric', 'N', 'N05'),
--   ('N05C', 'Psycholeptics drugs', 'Hypnotics and sedatives drugs', 'Psychiatric', 'N', 'N05'),
--   ('R03', 'Drugs for obstructive airway diseases', 'Obstructive airway disease drugs', 'Respiratory', 'R', 'R03'),
--   ('R06', 'Antihistamines for systemic use', 'Antihistamines for systemic use', 'Allergy', 'R', 'R06');
