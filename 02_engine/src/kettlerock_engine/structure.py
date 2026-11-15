"""Milestone 1: structure tables.

dim_market, dim_store, dim_product, dim_account, dim_scenario, dim_debt_facility and
the opening rows of fact_cost_history. Structure is deterministic: identifiers and
attributes come from the frozen masters in config/structure and from calibrated
parameters, never from random draws, so they are identical in every regeneration.
"""
from pathlib import Path
import pandas as pd
from .params import Params

REGION_RENT = {"Greater Toronto Area": "SE-11a", "Southwestern Ontario": "SE-11b",
               "Montreal area": "SE-11c", "Atlantic Canada": "SE-11d"}
LOCATION_MULT = {"urban": "SE-11e", "suburban": "SE-11f", "small town": "SE-11g"}
CATEGORY_IDS = {"Consumables": "CAT-CON", "General merchandise": "CAT-GM", "Seasonal": "CAT-SEA"}


def build_dim_store(structure_dir: Path, params: Params) -> pd.DataFrame:
    s = pd.read_csv(structure_dir / "stores_master.csv", dtype=str, keep_default_na=False)
    rate = s["region"].map(lambda r: params.value(REGION_RENT[r]))
    mult = s["location_type"].map(lambda l: params.value(LOCATION_MULT[l]))
    s["occupancy_cost_per_sq_ft"] = (rate * mult).round(2)
    s["annual_occupancy_cost"] = (s["occupancy_cost_per_sq_ft"] * s["selling_sq_ft"].astype(int)).round(2)
    return s


def build_dim_market(dim_store: pd.DataFrame) -> pd.DataFrame:
    g = dim_store.groupby("market_id")
    m = pd.DataFrame({
        "region": g["region"].first(), "province": g["province"].first(), "city": g["city"].first(),
        "stores_open": g["status"].apply(lambda x: int((x == "open").sum())),
        "stores_including_planned": g.size(),
    }).reset_index()
    return m


def build_dim_product(structure_dir: Path) -> pd.DataFrame:
    p = pd.read_csv(structure_dir / "products_master.csv", dtype=str, keep_default_na=False)
    depts = list(dict.fromkeys(p["department"]))          # order of first appearance
    p.insert(2, "category_id", p["category"].map(CATEGORY_IDS))
    p.insert(4, "department_id", p["department"].map({d: f"D{i:02d}" for i, d in enumerate(depts, 1)}))
    return p


def build_fact_cost_history(dim_product: pd.DataFrame) -> pd.DataFrame:
    """Opening cost row per item; later rows (supplier and freight changes) come from the world draw."""
    return pd.DataFrame({
        "product_id": dim_product["product_id"], "effective_date": dim_product["launch_date"],
        "supplier_cost": dim_product["base_supplier_cost"], "supplier_currency": dim_product["supplier_currency"],
        "inbound_freight_rate": dim_product["inbound_freight_rate"], "duty_tariff_rate": dim_product["duty_tariff_rate"],
        "change_reason": "opening cost",
    })


ACCOUNTS = [
    # account_id, account_name, level_1 (section 8 hierarchy), sign
    ("4000", "Gross sales", "Net sales", 1), ("4100", "Promotional discounts", "Net sales", -1),
    ("4200", "Markdowns", "Net sales", -1), ("4300", "Returns", "Net sales", -1),
    ("5000", "Landed cost of units sold", "Cost of goods", -1), ("5100", "Shrink", "Cost of goods", -1),
    ("5200", "Inventory write-downs", "Cost of goods", -1), ("5300", "Supplier rebates", "Cost of goods", 1),
    ("6000", "Store labour", "Store costs", -1), ("6100", "Occupancy", "Store costs", -1),
    ("6200", "Other store costs", "Store costs", -1),
    ("7000", "Distribution", "Company costs", -1), ("7100", "Marketing", "Company costs", -1),
    ("7200", "Head office", "Company costs", -1),
    ("8000", "Pre-opening costs", "Below adjusted EBITDA", -1), ("8100", "One-off items", "Below adjusted EBITDA", -1),
    ("8200", "Depreciation", "Below adjusted EBITDA", -1),
    ("9000", "Interest", "Below operating income", -1), ("9100", "FX transaction gains and losses", "Below operating income", 1),
    ("9200", "Income tax", "Below operating income", -1),
]


def build_dim_account() -> pd.DataFrame:
    return pd.DataFrame(ACCOUNTS, columns=["account_id", "account_name", "account_group", "sign"])


def build_dim_scenario(structure_dir: Path) -> pd.DataFrame:
    return pd.read_csv(structure_dir / "scenarios.csv", dtype=str, keep_default_na=False)


def build_dim_debt_facility(params: Params) -> pd.DataFrame:
    return pd.DataFrame([
        {"facility_id": "TERM", "facility_name": "Term loan", "original_amount": params.value("CAP-01"),
         "facility_limit": "", "annual_amortization_pct": params.value("CAP-02"), "spread_over_base_pp": params.value("CAP-04"),
         "covenant_max_leverage": params.value("CAP-05"), "internal_headroom": params.value("CAP-06")},
        {"facility_id": "RCF", "facility_name": "Revolving credit facility", "original_amount": "",
         "facility_limit": params.value("CAP-03"), "annual_amortization_pct": "", "spread_over_base_pp": params.value("CAP-04"),
         "covenant_max_leverage": params.value("CAP-05"), "internal_headroom": params.value("CAP-06")},
    ])
