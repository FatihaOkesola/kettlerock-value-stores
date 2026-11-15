"""Structure is deterministic: two builds give byte-identical canonical files and stable identifiers."""
from kettlerock_engine.build import build_structure
from kettlerock_engine.outputs import write_table


def test_two_builds_identical(cfg, tmp_path):
    a = {n: write_table(df, n, tmp_path / "a") for n, df in build_structure(cfg).items()}
    b = {n: write_table(df, n, tmp_path / "b") for n, df in build_structure(cfg).items()}
    assert {n: e["sha256"] for n, e in a.items()} == {n: e["sha256"] for n, e in b.items()}


def test_identifiers_unique(tables):
    keys = {"dim_store": "store_id", "dim_product": "product_id", "dim_market": "market_id",
            "dim_date": "date_id", "dim_holiday": "holiday_id", "dim_account": "account_id",
            "dim_scenario": "scenario_id", "dim_debt_facility": "facility_id"}
    for table, key in keys.items():
        assert tables[table][key].is_unique, table
