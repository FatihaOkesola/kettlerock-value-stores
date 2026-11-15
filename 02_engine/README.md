# Kettlerock engine

The engine builds Kettlerock's synthetic data from the calibrated parameters in `01_calibration`. It is a small Python package: `src/kettlerock_engine` holds the code, `tests/` verifies it with pytest, and `notebooks/engine_walkthrough.ipynb` runs it step by step with explanations.

| Folder | Contents |
| --- | --- |
| `src/kettlerock_engine/` | Engine modules, one per stage of the generation order |
| `config/engine.toml` | Paths to the calibration files (read in place, never copied) |
| `config/structure/` | Authored structure: store list, product catalogue, closure rules, planning versions |
| `tools/` | Scripts that produced the structure files; re-running them reproduces the files byte for byte |
| `schemas/` | PostgreSQL table definitions and the `COPY` loader |
| `tests/` | Automated checks against the specification and the calibrated parameters |

## Running it

From the `02_engine` folder, with Python 3.11 or later:

```
pip install -e .[dev]
python -m kettlerock_engine.build
python -m pytest
```

The build writes canonical CSV files and `manifest.csv` (each file's SHA-256 hash and row count) to `output/csv`. These files are the single source of truth; PostgreSQL is loaded from them with `schemas/load_structure.sql`, and the loaded row counts are checked against the manifest.
