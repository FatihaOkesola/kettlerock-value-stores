-- Load the trading history from the canonical CSVs, then check row counts against manifest.csv.
-- Run from the 02_engine folder with psql:  psql -d kettlerock -f schemas/load_history.sql
SET search_path TO kettlerock;

\copy fact_traffic_day FROM 'output/csv/fact_traffic_day.csv' WITH (FORMAT csv, HEADER true, NULL '')

-- Post-load check: the count must equal the rows column for fact_traffic_day.csv in output/csv/manifest.csv
SELECT 'fact_traffic_day' AS table_name, COUNT(*) AS loaded_rows FROM fact_traffic_day;

-- Closed days carry no transactions
SELECT trading_status, COUNT(*) AS days, SUM(transactions) AS transactions
FROM fact_traffic_day GROUP BY trading_status ORDER BY trading_status;
