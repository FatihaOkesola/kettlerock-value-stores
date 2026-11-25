"""Engine configuration: paths to calibration inputs, structure files and outputs."""
from dataclasses import dataclass
from pathlib import Path
import tomllib

ENGINE_ROOT = Path(__file__).resolve().parents[2]   # the 02_engine folder


@dataclass(frozen=True)
class Config:
    calibrated_parameters: Path
    calibrated_vectors: Path
    calibration_sources: Path
    structure_dir: Path
    output_dir: Path
    specification: Path
    sealed_dir: Path
    commitment_dir: Path
    first_fiscal_year: int
    last_fiscal_year: int
    history_last_fiscal_year: int
    history_last_fiscal_quarter: int


def load_config(path: Path | None = None) -> Config:
    path = path or ENGINE_ROOT / "config" / "engine.toml"
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    p = raw["paths"]
    return Config(
        calibrated_parameters=(ENGINE_ROOT / p["calibrated_parameters"]).resolve(),
        calibrated_vectors=(ENGINE_ROOT / p["calibrated_vectors"]).resolve(),
        calibration_sources=(ENGINE_ROOT / p["calibration_sources"]).resolve(),
        structure_dir=(ENGINE_ROOT / p["structure_dir"]).resolve(),
        output_dir=(ENGINE_ROOT / p["output_dir"]).resolve(),
        specification=(ENGINE_ROOT / p["specification"]).resolve(),
        sealed_dir=(ENGINE_ROOT / p["sealed_dir"]).resolve(),
        commitment_dir=(ENGINE_ROOT / p["commitment_dir"]).resolve(),
        first_fiscal_year=raw["calendar"]["first_fiscal_year"],
        last_fiscal_year=raw["calendar"]["last_fiscal_year"],
        history_last_fiscal_year=raw["history"]["last_fiscal_year"],
        history_last_fiscal_quarter=raw["history"]["last_fiscal_quarter"],
    )
