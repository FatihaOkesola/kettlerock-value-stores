"""No public output may contain a sealed parameter ID or a sealed value.

The effect of a sealed value will show in the generated data, which is the point of
the analysis; the value itself is never written to a public file. Sealed values are
written to ten decimal places, so a match in a public file cannot be a coincidence.

These checks run against the real sealed file on the machine that holds it, and are
skipped everywhere else.
"""
import re
from pathlib import Path

import pandas as pd
import pytest

from kettlerock_engine.config import ENGINE_ROOT


def _public_files(cfg):
    folders = [cfg.output_dir, ENGINE_ROOT / "notebooks", cfg.commitment_dir, ENGINE_ROOT / "data"]
    for folder in folders:
        if folder.exists():
            yield from (p for p in folder.rglob("*") if p.is_file())


def test_loader_reads_only_canonical_csvs():
    sql = (ENGINE_ROOT / "schemas" / "load_structure.sql").read_text(encoding="utf-8")
    sources = re.findall(r"FROM '([^']+)'", sql)
    assert sources and all(s.startswith("output/csv/") for s in sources)


def test_public_outputs_hold_no_sealed_values(cfg):
    sealed_file = cfg.sealed_dir / "sealed_world.csv"
    if not sealed_file.exists():
        pytest.skip("No sealed file on this machine")
    sealed = pd.read_csv(sealed_file, dtype=str, keep_default_na=False)
    secrets_ = set(sealed.value[sealed.value.str.fullmatch(r"-?\d+\.\d{10}")])
    ids = set(sealed.sealed_parameter_id)
    for path in _public_files(cfg):
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not any(i in text for i in ids), f"{path.name} contains a sealed parameter ID"
        assert not any(v in text for v in secrets_), f"{path.name} contains a sealed value"


def test_sealed_folder_sits_outside_public_folders(cfg):
    for public in [cfg.output_dir, ENGINE_ROOT / "notebooks", cfg.commitment_dir]:
        assert public not in cfg.sealed_dir.parents and public != cfg.sealed_dir
