"""Table and CSV export helpers shared across analysis scripts."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

import numpy as np
import pandas as pd

__all__ = [
    "ensure_directory",
    "write_csv",
    "write_table",
    "write_manuscript_table",
    "build_ceaf_table",
    "build_vbp_table",
    "build_probability_threshold_table",
]


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(df: pd.DataFrame, path: Path, *, index: bool = False) -> Path:
    ensure_directory(path.parent)
    df.to_csv(path, index=index)
    return path


def write_table(df: pd.DataFrame, outdir: Path, filename: str, *, index: bool = False) -> Path:
    ensure_directory(outdir)
    path = outdir / filename
    df.to_csv(path, index=index)
    return path


def write_manuscript_table(df: pd.DataFrame, filename: str, *, index: bool = False) -> Path:
    """Write a clean CSV table to tables_for_manuscript/ directory for journal submission."""
    manuscript_dir = Path("tables_for_manuscript")
    ensure_directory(manuscript_dir)
    path = manuscript_dir / filename
    df.to_csv(path, index=index)
    return path


def build_ceaf_table(probabilities_df: pd.DataFrame, ceaf_df: pd.DataFrame, *, metadata: Optional[Mapping[str, Any]] = None) -> pd.DataFrame:
    """Return a tidy table summarising CEAF results per λ."""

    summary = ceaf_df.copy()
    summary = summary.rename(
        columns={
            "ceaf_strategy": "strategy",
            "ceaf_probability": "probability",
            "ceaf_expected_nmb": "expected_nmb",
        }
    )
    summary["probability_percent"] = 100.0 * summary["probability"]
    if metadata:
        for key, value in metadata.items():
            summary[key] = value
    summary.sort_values("lambda", inplace=True)
    summary.reset_index(drop=True, inplace=True)
    return summary


def build_vbp_table(vbp_df: pd.DataFrame, *, metadata: Optional[Mapping[str, Any]] = None) -> pd.DataFrame:
    """Normalise column names and append metadata for manuscript tables."""

    table = vbp_df.copy()
    table = table.rename(
        columns={
            "lambda": "willingness_to_pay",
            "p_star": "value_based_price",
            "E_Ei": "expected_effect",
            "E_Ki": "expected_adjusted_cost",
            "expected_nmb_best_excl_focal": "best_competitor_expected_nmb",
        }
    )
    if metadata:
        for key, value in metadata.items():
            table[key] = value
    ordered_columns = [
        "willingness_to_pay",
        "value_based_price",
        "expected_effect",
        "expected_adjusted_cost",
        "best_competitor_expected_nmb",
    ] + sorted(set(table.columns) - {
        "willingness_to_pay",
        "value_based_price",
        "expected_effect",
        "expected_adjusted_cost",
        "best_competitor_expected_nmb",
    })
    table = table.loc[:, ordered_columns]
    table.sort_values("willingness_to_pay", inplace=True)
    table.reset_index(drop=True, inplace=True)
    return table


def _interpolate_threshold(sub: pd.DataFrame, threshold: float, price_col: str, prob_col: str) -> float | None:
    ordered = sub.sort_values(price_col)
    probabilities = ordered[prob_col].to_numpy(dtype=float)
    prices = ordered[price_col].to_numpy(dtype=float)
    mask = probabilities >= threshold
    if not mask.any():
        return None
    idx = int(mask.argmax())
    if idx == 0:
        return float(prices[0])
    p1, p2 = probabilities[idx - 1], probabilities[idx]
    price1, price2 = prices[idx - 1], prices[idx]
    if np.isclose(p1, p2):
        return float(price2)
    weight = (threshold - p1) / (p2 - p1)
    return float(price1 + weight * (price2 - price1))


def build_probability_threshold_table(
    probability_df: pd.DataFrame,
    *,
    group_col: str,
    price_col: str,
    prob_col: str,
    threshold: float = 0.5,
    metadata: Optional[Mapping[str, Any]] = None,
) -> pd.DataFrame:
    """Summarise the price at which each therapy reaches the target probability."""

    records = []
    for group_value, sub_df in probability_df.groupby(group_col):
        threshold_price = _interpolate_threshold(sub_df, threshold, price_col, prob_col)
        records.append(
            {
                group_col: group_value,
                "threshold": threshold,
                "threshold_price": threshold_price,
            }
        )
    result = pd.DataFrame(records)
    if metadata:
        for key, value in metadata.items():
            result[key] = value
    result.sort_values(group_col, inplace=True)
    result.reset_index(drop=True, inplace=True)
    return result
