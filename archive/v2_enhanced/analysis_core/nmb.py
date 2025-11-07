"""Net monetary benefit calculations and deterministic decision rules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
import pandas as pd


@dataclass
class NMBResult:
    nmb_cube: pd.DataFrame
    expected: pd.DataFrame
    optimal: pd.Series


def compute_nmb(psa_table: pd.DataFrame, lambda_values: Iterable[float], focal: Optional[str] = None) -> NMBResult:
    """Compute NMB for each draw/strategy across a λ grid."""

    lambda_array = np.atleast_1d(np.array(list(lambda_values), dtype=float))
    if lambda_array.size == 0:
        raise ValueError("Lambda grid must contain at least one value")
    if np.any(~np.isfinite(lambda_array)):
        raise ValueError("Lambda values must be finite")

    cost = psa_table.pivot(index="draw", columns="strategy", values="cost")
    effect = psa_table.pivot(index="draw", columns="strategy", values="effect")

    nmb_layers = []
    expected_rows = []
    optimal_rows = []

    for lam in lambda_array:
        nmb = lam * effect - cost
        nmb["lambda"] = lam
        nmb_layers.append(nmb.set_index("lambda", append=True))
        expected_rows.append((lam, nmb.drop(columns="lambda").mean(axis=0)))
        optimal_rows.append((lam, argmax_with_tiebreak(nmb.drop(columns="lambda"), focal=focal)))

    nmb_cube = pd.concat(nmb_layers).reorder_levels(["lambda", "draw"]).sort_index()
    expected = pd.DataFrame(dict(expected_rows)).T
    optimal = pd.Series({lam: series for lam, series in optimal_rows})

    return NMBResult(nmb_cube=nmb_cube, expected=expected, optimal=optimal)


def argmax_with_tiebreak(nmb_df: pd.DataFrame, focal: Optional[str] = None) -> pd.Series:
    """Per-draw optimal strategy with deterministic tie-breaking."""

    strategies = list(nmb_df.columns)
    values = nmb_df.to_numpy()
    max_indices = np.argmax(values, axis=1)
    max_values = values[np.arange(values.shape[0]), max_indices]

    if focal is not None and focal in strategies:
        focal_idx = strategies.index(focal)
        focal_values = values[:, focal_idx]
        is_tied = np.isclose(focal_values, max_values)
        max_indices = np.where(is_tied, focal_idx, max_indices)
        max_values = np.where(is_tied, focal_values, max_values)

    for idx, strategy in sorted(enumerate(strategies), key=lambda x: x[1]):
        strategy_values = values[:, idx]
        is_equal = np.isclose(strategy_values, max_values)
        max_indices = np.where(is_equal, idx, max_indices)

    optimal = pd.Series([strategies[i] for i in max_indices], index=nmb_df.index)
    return optimal