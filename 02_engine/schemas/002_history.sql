-- Milestone 3 onward: trading history. Loaded from the canonical CSVs in output/csv with COPY (see load_history.sql).
-- Run after 001_structure.sql.
CREATE SCHEMA IF NOT EXISTS kettlerock;
SET search_path TO kettlerock;

-- One row per store per day from the store's opening date to the Q3 FY2027 close, closed days included.
-- trading_status: open, reduced_hours, closed_holiday, closed_remodel, closed_unplanned.
DROP TABLE IF EXISTS fact_traffic_day CASCADE;
CREATE TABLE fact_traffic_day (
    date_id INTEGER NOT NULL,
    date DATE NOT NULL,
    store_id TEXT NOT NULL,
    trading_status TEXT NOT NULL,
    transactions INTEGER NOT NULL CHECK (transactions >= 0),
    PRIMARY KEY (store_id, date_id)
);
