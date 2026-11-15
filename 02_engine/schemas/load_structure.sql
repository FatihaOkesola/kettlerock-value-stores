-- Load the canonical CSVs into PostgreSQL, then check row counts against manifest.csv.
-- Run from the 02_engine folder with psql:  psql -d kettlerock -f schemas/load_structure.sql
SET search_path TO kettlerock;

\copy dim_date FROM 'output/csv/dim_date.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy dim_holiday FROM 'output/csv/dim_holiday.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy dim_market FROM 'output/csv/dim_market.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy dim_store FROM 'output/csv/dim_store.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy dim_product FROM 'output/csv/dim_product.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy fact_cost_history FROM 'output/csv/fact_cost_history.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy dim_account FROM 'output/csv/dim_account.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy dim_scenario FROM 'output/csv/dim_scenario.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy dim_debt_facility FROM 'output/csv/dim_debt_facility.csv' WITH (FORMAT csv, HEADER true, NULL '')

-- Post-load check: each count must equal the rows column in output/csv/manifest.csv
SELECT 'dim_date' AS table_name, COUNT(*) AS loaded_rows FROM dim_date
UNION ALL SELECT 'dim_holiday', COUNT(*) FROM dim_holiday
UNION ALL SELECT 'dim_market', COUNT(*) FROM dim_market
UNION ALL SELECT 'dim_store', COUNT(*) FROM dim_store
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'fact_cost_history', COUNT(*) FROM fact_cost_history
UNION ALL SELECT 'dim_account', COUNT(*) FROM dim_account
UNION ALL SELECT 'dim_scenario', COUNT(*) FROM dim_scenario
UNION ALL SELECT 'dim_debt_facility', COUNT(*) FROM dim_debt_facility;
