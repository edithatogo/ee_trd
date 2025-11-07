from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analysis_core.io import PSAData


@dataclass
class DeltaDF:
    therapy: str
    df: pd.DataFrame  # columns: draw, dE, dC


def compute_deltas(psa: PSAData, therapy: str) -> DeltaDF:
    """Compute per-draw ΔE and ΔC for a therapy relative to base.

    Returns a dataframe with columns: draw, dE, dC.
    """
    base = psa.config.base
    df = psa.table.copy()
    d_base = df[df["strategy"] == base].set_index("draw")["effect"].rename("E_base")
    c_base = df[df["strategy"] == base].set_index("draw")["cost"].rename("C_base")

    d_t = (
        df[df["strategy"] == therapy]
        .set_index("draw")[
            ["effect", "cost"]
        ]
        .rename(columns={"effect": "E_i", "cost": "C_i"})
    )

    merged = d_t.join(d_base, how="inner").join(c_base, how="inner").reset_index()
    merged["dE"] = merged["E_i"] - merged["E_base"]
    merged["dC"] = merged["C_i"] - merged["C_base"]
    out = merged[["draw", "dE", "dC"]].copy()
    return DeltaDF(therapy=therapy, df=out)
