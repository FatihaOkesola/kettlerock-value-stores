"""Canonical CSV output and the manifest.

The CSV files written here are the single source of truth. Every file is written
with fixed formatting so the same inputs always produce the same bytes, and its
SHA-256 hash and row count are recorded in manifest.csv.
"""
from pathlib import Path
import hashlib
import pandas as pd


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_table(df: pd.DataFrame, name: str, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.csv"
    df.to_csv(path, index=False, lineterminator="\n", encoding="utf-8")
    return {"file": path.name, "sha256": sha256_file(path), "rows": len(df)}


def write_manifest(entries: list[dict], out_dir: Path) -> Path:
    manifest = pd.DataFrame(entries).sort_values("file").reset_index(drop=True)
    path = out_dir / "manifest.csv"
    manifest.to_csv(path, index=False, lineterminator="\n")
    return path
