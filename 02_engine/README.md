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
| `commitment/` | The published seal: `commitment_manifest.csv` and the `commitments.csv` ledger |

## Running it

From the `02_engine` folder, with Python 3.11 or later:

```
pip install -e .[dev]
python -m kettlerock_engine.build
python -m pytest
```

The build writes canonical CSV files and `manifest.csv` (each file's SHA-256 hash and row count) to `output/csv`. It always builds the structure tables; the trading history (`fact_traffic_day` and later tables) is built only when the seal described below verifies. These files are the single source of truth; PostgreSQL tables are created with `schemas/001_structure.sql` and `schemas/002_history.sql` and loaded with `schemas/load_structure.sql` and `schemas/load_history.sql`, and the loaded row counts are checked against the manifest.

## The sealed world

Some drivers of the history are hidden from the analyst until the planning season ends. Their ranges and rules are public in `calibrated_parameters.csv`; the values actually used are drawn once from a private 256-bit seed and frozen in `sealed/sealed_world.csv`.

```
python -m kettlerock_engine.seal --commit <40-character GitHub commit SHA>
python -m kettlerock_engine.seal --verify
```

Sealing runs after the final GitHub commit of the calibration, specification and engine, and records that commit. `commitment/commitment_manifest.csv` publishes separate SHA-256 hashes of the exact bytes of the seed and the sealed file, with the commit, the engine version and the hashes of the calibration files and specification. The sealed file is canonical: UTF-8, rows sorted by key, numbers at ten decimal places, `\n` line endings and no timestamps.

History is built only when the private files match the published hashes and the seed reproduces the sealed file exactly under the current inputs. Later edits to the specification or calibration files are reported but allowed, because the redraw check fails if any of them would change a sealed value. A seal is never overwritten: a correction adds a new commitment to `commitments.csv` with the reason the earlier one was replaced. No public output contains a sealed parameter ID or value (`tests/test_leak.py`). After the season, the seed and sealed file are released so anyone can recompute the hashes and regenerate the world.
