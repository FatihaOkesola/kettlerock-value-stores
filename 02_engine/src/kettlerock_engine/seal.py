"""Milestone 2: seal the hidden world and publish the commitment.

Seal (once, after the final GitHub commit of the calibration, specification and engine):
    python -m kettlerock_engine.seal --commit <40-character commit SHA>

Check the seal at any time (later milestones run this before building history):
    python -m kettlerock_engine.seal --verify

Replace a seal (only to correct an error; the old files are kept, never overwritten):
    python -m kettlerock_engine.seal --commit <SHA> --replace --reason "<why the earlier seal was invalid>"

Private (sealed/, never uploaded): seed.txt and sealed_world.csv.
Public (commitment/, uploaded to GitHub): commitment_manifest.csv and commitments.csv.
"""
from __future__ import annotations

import argparse
import csv
import re
import secrets
import shutil
from datetime import date
from pathlib import Path

from . import __version__
from .build import build_structure
from .config import Config, load_config
from .outputs import sha256_file
from .params import Params
from .world import draw_world

SEED_FILE = "seed.txt"
SEALED_FILE = "sealed_world.csv"
MANIFEST_FILE = "commitment_manifest.csv"
LEDGER_FILE = "commitments.csv"
LEDGER_COLUMNS = ["commitment_version", "sealed_on", "git_commit", "engine_version", "seed_sha256",
                  "sealed_world_sha256", "status", "replaced_reason"]


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def _input_hashes(cfg: Config) -> dict:
    return {"calibrated_parameters_sha256": sha256_file(cfg.calibrated_parameters),
            "calibrated_vectors_sha256": sha256_file(cfg.calibrated_vectors),
            "specification_sha256": sha256_file(cfg.specification)}


def _read_ledger(cfg: Config) -> list[dict]:
    path = cfg.commitment_dir / LEDGER_FILE
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def read_manifest(cfg: Config) -> dict:
    path = cfg.commitment_dir / MANIFEST_FILE
    if not path.exists():
        raise FileNotFoundError("No commitment manifest: the world has not been sealed yet.")
    with open(path, newline="", encoding="utf-8") as f:
        return {r["field"]: r["value"] for r in csv.DictReader(f)}


def seal(commit: str, cfg: Config | None = None, replace: bool = False, reason: str = "") -> dict:
    cfg = cfg or load_config()
    if not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
        raise ValueError("Give the full 40-character commit SHA from GitHub (lowercase letters and digits).")
    seed_path, sealed_path = cfg.sealed_dir / SEED_FILE, cfg.sealed_dir / SEALED_FILE
    ledger = _read_ledger(cfg)

    if sealed_path.exists() or ledger:
        if not replace:
            raise RuntimeError("The world is already sealed. A seal is never overwritten; "
                               "use --replace with --reason only to correct an error.")
        if not reason.strip():
            raise ValueError("A replacement needs a --reason saying why the earlier seal is invalid.")
        old_version = int(ledger[-1]["commitment_version"]) if ledger else 0
        archive = cfg.sealed_dir / f"v{old_version}"
        archive.mkdir(parents=True, exist_ok=False)
        for p in (seed_path, sealed_path):
            if p.exists():
                shutil.move(str(p), archive / p.name)
        for row in ledger:
            if row["status"] == "active":
                row["status"] = "replaced"
                row["replaced_reason"] = reason.strip()

    # 1. Private seed: 256 bits from the operating system's secure random source
    _write_bytes(seed_path, (secrets.token_hex(32) + "\n").encode("ascii"))
    seed_hex = seed_path.read_text(encoding="ascii").strip()

    # 2. Draw and freeze the sealed world
    params = Params(cfg.calibrated_parameters, cfg.calibrated_vectors)
    _write_bytes(sealed_path, draw_world(seed_hex, params, build_structure(cfg)))

    # 3. The commitment: separate hashes of the exact bytes of each private file
    version = len(ledger) + 1
    manifest = {"commitment_version": str(version), "git_commit": commit, "engine_version": __version__,
                "seed_sha256": sha256_file(seed_path), "sealed_world_sha256": sha256_file(sealed_path),
                **_input_hashes(cfg)}
    _write_csv(cfg.commitment_dir / MANIFEST_FILE, ["field", "value"],
               [{"field": k, "value": v} for k, v in manifest.items()])
    ledger.append({"commitment_version": str(version), "sealed_on": date.today().isoformat(), "git_commit": commit,
                   "engine_version": __version__, "seed_sha256": manifest["seed_sha256"],
                   "sealed_world_sha256": manifest["sealed_world_sha256"], "status": "active", "replaced_reason": ""})
    _write_csv(cfg.commitment_dir / LEDGER_FILE, LEDGER_COLUMNS, ledger)
    return manifest


def verify_seal(cfg: Config | None = None) -> dict:
    """Raise if the private files no longer match the commitment or the seed no longer reproduces them.

    Changes to the specification or calibration files after sealing are reported as warnings:
    they matter only if they change a sealed draw, and the redraw check catches that.
    """
    cfg = cfg or load_config()
    m = read_manifest(cfg)
    seed_path, sealed_path = cfg.sealed_dir / SEED_FILE, cfg.sealed_dir / SEALED_FILE
    problems = []
    for path, key in [(seed_path, "seed_sha256"), (sealed_path, "sealed_world_sha256")]:
        if not path.exists():
            problems.append(f"{path.name} is missing from {cfg.sealed_dir}")
        elif sha256_file(path) != m[key]:
            problems.append(f"{path.name} does not match its published hash")
    warnings = [f"{key.replace('_sha256', '')} has changed since sealing; the sealed draws are still checked by redrawing"
                for key, value in _input_hashes(cfg).items() if value != m[key]]
    if not problems:
        params = Params(cfg.calibrated_parameters, cfg.calibrated_vectors)
        redrawn = draw_world(seed_path.read_text(encoding="ascii").strip(), params, build_structure(cfg))
        if redrawn != sealed_path.read_bytes():
            problems.append("redrawing from the seed does not reproduce the sealed file")
    if problems:
        raise RuntimeError("Seal check failed: " + "; ".join(problems))
    return {**m, "warnings": warnings}


def main():
    ap = argparse.ArgumentParser(description="Seal the hidden world or verify the seal.")
    ap.add_argument("--commit", help="40-character GitHub commit SHA the seal is drawn from")
    ap.add_argument("--verify", action="store_true", help="check the seal against the published commitment")
    ap.add_argument("--replace", action="store_true", help="replace an existing seal (keeps the old files)")
    ap.add_argument("--reason", default="", help="why an earlier seal is replaced")
    a = ap.parse_args()
    if a.verify:
        m = verify_seal()
        print(f"Seal verified: commitment version {m['commitment_version']}, commit {m['git_commit'][:12]}.")
        print("Seed and sealed file match their hashes, and the seed reproduces the sealed file exactly.")
        for w in m["warnings"]:
            print(f"Note: {w}.")
        return
    m = seal(a.commit, replace=a.replace, reason=a.reason)
    print(f"Sealed. Commitment version {m['commitment_version']} for commit {m['git_commit'][:12]}.")
    print(f"  seed_sha256          {m['seed_sha256']}")
    print(f"  sealed_world_sha256  {m['sealed_world_sha256']}")
    print("Upload only the two files in 02_engine/commitment/ to GitHub.")
    print("Keep 02_engine/sealed/ private and back it up encrypted.")


if __name__ == "__main__":
    main()
