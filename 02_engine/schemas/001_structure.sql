-- Milestone 1: structure tables. Loaded from the canonical CSVs in output/csv with COPY (see load_structure.sql).
CREATE SCHEMA IF NOT EXISTS kettlerock;
SET search_path TO kettlerock;

DROP TABLE IF EXISTS dim_date CASCADE;
CREATE TABLE dim_date (
    date_id INTEGER,
    date DATE,
    day_of_week TEXT,
    day_of_week_num INTEGER,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    fiscal_month INTEGER,
    fiscal_month_name TEXT,
    fiscal_week INTEGER,
    fiscal_day_of_year INTEGER,
    is_53_week_year INTEGER,
    calendar_year INTEGER,
    calendar_month INTEGER,
    PRIMARY KEY (date_id)
);

DROP TABLE IF EXISTS dim_holiday CASCADE;
CREATE TABLE dim_holiday (
    holiday_id TEXT,
    date DATE,
    calendar_year INTEGER,
    province TEXT,
    holiday_key TEXT,
    holiday_name TEXT,
    trading_status TEXT,
    legal_basis TEXT,
    source_id TEXT,
    PRIMARY KEY (holiday_id)
);

DROP TABLE IF EXISTS dim_market CASCADE;
CREATE TABLE dim_market (
    market_id TEXT,
    region TEXT,
    province TEXT,
    city TEXT,
    stores_open INTEGER,
    stores_including_planned INTEGER,
    PRIMARY KEY (market_id)
);

DROP TABLE IF EXISTS dim_store CASCADE;
CREATE TABLE dim_store (
    store_id TEXT,
    store_name TEXT,
    market_id TEXT,
    region TEXT,
    province TEXT,
    city TEXT,
    location_type TEXT,
    format TEXT,
    selling_sq_ft INTEGER,
    open_date DATE,
    status TEXT,
    cohort_year INTEGER,
    lease_term_start DATE,
    lease_term_end DATE,
    lease_renewals_taken INTEGER,
    remodel_reopen_date DATE,
    occupancy_cost_per_sq_ft NUMERIC(10,2),
    annual_occupancy_cost NUMERIC(14,2),
    PRIMARY KEY (store_id)
);

DROP TABLE IF EXISTS dim_product CASCADE;
CREATE TABLE dim_product (
    product_id TEXT,
    product_name TEXT,
    category_id TEXT,
    category TEXT,
    department_id TEXT,
    department TEXT,
    price_point NUMERIC(6,2),
    import_flag SMALLINT,
    supplier_currency TEXT,
    base_supplier_cost NUMERIC(12,4),
    inbound_freight_rate NUMERIC(8,4),
    duty_tariff_rate NUMERIC(8,4),
    base_landed_cost_cad NUMERIC(12,4),
    product_margin_at_ticket NUMERIC(8,4),
    seasonal_window NUMERIC,
    launch_date DATE,
    discontinue_date DATE,
    PRIMARY KEY (product_id)
);

DROP TABLE IF EXISTS fact_cost_history CASCADE;
CREATE TABLE fact_cost_history (
    product_id TEXT,
    effective_date DATE,
    supplier_cost NUMERIC(12,4),
    supplier_currency TEXT,
    inbound_freight_rate NUMERIC(8,4),
    duty_tariff_rate NUMERIC(8,4),
    change_reason TEXT,
    PRIMARY KEY (product_id, effective_date)
);

DROP TABLE IF EXISTS dim_account CASCADE;
CREATE TABLE dim_account (
    account_id TEXT,
    account_name TEXT,
    account_group TEXT,
    sign SMALLINT,
    PRIMARY KEY (account_id)
);

DROP TABLE IF EXISTS dim_scenario CASCADE;
CREATE TABLE dim_scenario (
    scenario_id TEXT,
    scenario_type TEXT,
    case TEXT,
    planning_cycle TEXT,
    as_of_date DATE,
    actuals_through DATE,
    version_status TEXT,
    assumption_set_id TEXT,
    prepared_by TEXT,
    PRIMARY KEY (scenario_id)
);

DROP TABLE IF EXISTS dim_debt_facility CASCADE;
CREATE TABLE dim_debt_facility (
    facility_id TEXT,
    facility_name TEXT,
    original_amount NUMERIC(16,2),
    "limit" NUMERIC(16,2),
    annual_amortization_pct NUMERIC(8,4),
    spread_over_base_pp NUMERIC(8,4),
    covenant_max_leverage NUMERIC(8,4),
    internal_headroom NUMERIC(8,4),
    PRIMARY KEY (facility_id)
);
