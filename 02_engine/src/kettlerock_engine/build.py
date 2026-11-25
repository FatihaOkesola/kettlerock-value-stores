"""Command-line entry point: python -m kettlerock_engine.build

Builds the structure tables (Milestone 1) and, once the world is sealed and the seal
verifies, the trading history (Milestone 3 onward). Every table is written as a canonical
CSV with its hash and row count in manifest.csv.
"""
from .config import load_config
from .params import Params
from .outputs import write_table, write_manifest
from . import calendar, structure


def build_structure(cfg=None):
    cfg = cfg or load_config()
    params = Params(cfg.calibrated_parameters, cfg.calibrated_vectors)
    dim_store = structure.build_dim_store(cfg.structure_dir, params)
    dim_product = structure.build_dim_product(cfg.structure_dir)
    return {
        "dim_date": calendar.build_dim_date(cfg.first_fiscal_year, cfg.last_fiscal_year),
        "dim_holiday": calendar.build_dim_holiday(cfg.structure_dir, cfg.first_fiscal_year, cfg.last_fiscal_year),
        "dim_store": dim_store,
        "dim_market": structure.build_dim_market(dim_store),
        "dim_product": dim_product,
        "fact_cost_history": structure.build_fact_cost_history(dim_product),
        "dim_account": structure.build_dim_account(),
        "dim_scenario": structure.build_dim_scenario(cfg.structure_dir),
        "dim_debt_facility": structure.build_dim_debt_facility(params),
    }


def build_history(cfg, params, tables) -> dict:
    """Trading history. Refuses to run unless the seal verifies (Milestone 2)."""
    from .seal import verify_seal, SEED_FILE, SEALED_FILE
    from .traffic import build_traffic
    m = verify_seal(cfg)
    seed_hex = (cfg.sealed_dir / SEED_FILE).read_text(encoding="ascii").strip()
    sealed_bytes = (cfg.sealed_dir / SEALED_FILE).read_bytes()
    for w in m["warnings"]:
        print(f"Note: {w}.")
    return {"fact_traffic_day": build_traffic(cfg, params, tables, seed_hex, sealed_bytes)}


def main():
    cfg = load_config()
    tables = build_structure(cfg)
    params = Params(cfg.calibrated_parameters, cfg.calibrated_vectors)
    try:
        tables.update(build_history(cfg, params, tables))
    except FileNotFoundError:
        print("Not sealed yet: built the structure tables only.")
    entries = [write_table(df, name, cfg.output_dir) for name, df in tables.items()]
    manifest = write_manifest(entries, cfg.output_dir)
    for e in entries:
        print(f"{e['file']:<28}{e['rows']:>8} rows  {e['sha256'][:12]}")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
