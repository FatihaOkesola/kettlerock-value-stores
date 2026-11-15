"""Read-only access to calibrated_parameters.csv and calibrated_parameter_vectors.csv.

Every business assumption the engine uses is read from these files by parameter_id;
none is typed into the code.
"""
from pathlib import Path
import pandas as pd


class Params:
    def __init__(self, parameters_csv: Path, vectors_csv: Path):
        self.table = pd.read_csv(parameters_csv, dtype=str, keep_default_na=False).set_index("parameter_id")
        self.vectors = pd.read_csv(vectors_csv, dtype={"parameter_id": str, "index_type": str, "index": str})

    def row(self, pid: str) -> pd.Series:
        if pid not in self.table.index:
            raise KeyError(f"Parameter {pid} is not in calibrated_parameters.csv")
        return self.table.loc[pid]

    def value(self, pid: str) -> float:
        """Central value as a number."""
        return float(self.row(pid)["central_value"])

    def bounds(self, pid: str) -> tuple[float, float]:
        r = self.row(pid)
        return float(r["lower_bound"]), float(r["upper_bound"])

    def vector(self, pid: str) -> pd.Series:
        """Multi-value parameter, normalised exactly: shares sum to 1, indexes average 1."""
        v = self.vectors[self.vectors.parameter_id == pid]
        if v.empty:
            raise KeyError(f"Vector {pid} is not in calibrated_parameter_vectors.csv")
        s = pd.Series(v["value"].astype(float).to_numpy(), index=v["index"].to_numpy())
        if v["index_type"].iloc[0] == "weekday":
            return s / s.sum()
        return s / s.mean()
