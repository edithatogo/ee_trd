"""
V4 Net Monetary Benefit Calculations

Consolidated from V2 analysis_core with enhancements.
Handles NMB calculations and deterministic decision rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
import pandas as pd


@dataclass
class NMBResult:
    """Container for NMB calculation results."""
    
    nmb_cube: pd.DataFrame  # NMB for each draw/strategy/lambda
    expected: pd.DataFrame  # Expected NMB for each strategy/lambda
    optimal: pd.Series      # Optimal strategy for each lambda


def compute_nmb(
    psa_table: pd.DataFrame,
    lambda_values: Iterable[float],
    focal: Optional[str] = None
) -> NMBResult:
    """
    Compute net monetary benefit for each draw/strategy across a λ grid.
    
    NMB = λ × Effect - Cost
    
    Args:
        psa_table: PSA data with columns: draw, strategy, cost, effect
        lambda_values: Willingness-to-pay threshold values
        focal: Optional focal strategy for tie-breaking
    
    Returns:
        NMBResult with NMB cube, expected values, and optimal strategies
    """
    lambda_array = np.atleast_1d(np.array(list(lambda_values), dtype=float))
    
    if lambda_array.size == 0:
        raise ValueError("Lambda grid must contain at least one value")
    
    if np.any(~np.isfinite(lambda_array)):
        raise ValueError("Lambda values must be finite")
    
    # Pivot data for vectorized computation
    cost = psa_table.pivot(index="draw", columns="strategy", values="cost")
    effect = psa_table.pivot(index="draw", columns="strategy", values="effect")
    
    nmb_layers = []
    expected_rows = []
    optimal_rows = []
    
    # Compute NMB for each lambda value
    for lam in lambda_array:
        # NMB = λ × E - C
        nmb = lam * effect - cost
        nmb["lambda"] = lam
        nmb_layers.append(nmb.set_index("lambda", append=True))
        
        # Expected NMB (mean across draws)
        expected_rows.append((lam, nmb.drop(columns="lambda").mean(axis=0)))
        
        # Optimal strategy per draw with tie-breaking
        optimal_rows.append(
            (lam, argmax_with_tiebreak(nmb.drop(columns="lambda"), focal=focal))
        )
    
    # Combine results
    nmb_cube = pd.concat(nmb_layers).reorder_levels(["lambda", "draw"]).sort_index()
    expected = pd.DataFrame(dict(expected_rows)).T
    optimal = pd.Series({lam: series for lam, series in optimal_rows})
    
    return NMBResult(nmb_cube=nmb_cube, expected=expected, optimal=optimal)


def argmax_with_tiebreak(
    nmb_df: pd.DataFrame,
    focal: Optional[str] = None
) -> pd.Series:
    """
    Determine optimal strategy per draw with deterministic tie-breaking.
    
    Tie-breaking rules:
    1. If focal strategy is tied for maximum, choose focal
    2. Otherwise, choose alphabetically first strategy among tied
    
    Args:
        nmb_df: NMB values with draws as rows, strategies as columns
        focal: Optional focal strategy for tie-breaking
    
    Returns:
        Series of optimal strategy names indexed by draw
    """
    strategies = list(nmb_df.columns)
    values = nmb_df.to_numpy()
    
    # Find maximum NMB per draw
    max_indices = np.argmax(values, axis=1)
    max_values = values[np.arange(values.shape[0]), max_indices]
    
    # Apply focal tie-breaking if specified
    if focal is not None and focal in strategies:
        focal_idx = strategies.index(focal)
        focal_values = values[:, focal_idx]
        is_tied = np.isclose(focal_values, max_values)
        max_indices = np.where(is_tied, focal_idx, max_indices)
        max_values = np.where(is_tied, focal_values, max_values)
    
    # Apply alphabetical tie-breaking
    for idx, strategy in sorted(enumerate(strategies), key=lambda x: x[1]):
        strategy_values = values[:, idx]
        is_equal = np.isclose(strategy_values, max_values)
        max_indices = np.where(is_equal, idx, max_indices)
    
    # Convert indices to strategy names
    optimal = pd.Series([strategies[i] for i in max_indices], index=nmb_df.index)
    
    return optimal


def calculate_incremental_nmb(
    nmb_df: pd.DataFrame,
    base_strategy: str,
    comparator_strategy: str
) -> pd.DataFrame:
    """
    Calculate incremental NMB between two strategies.
    
    Args:
        nmb_df: NMB values with draws as rows, strategies as columns
        base_strategy: Base strategy name
        comparator_strategy: Comparator strategy name
    
    Returns:
        DataFrame with incremental NMB values
    """
    if base_strategy not in nmb_df.columns:
        raise ValueError(f"Base strategy '{base_strategy}' not found")
    
    if comparator_strategy not in nmb_df.columns:
        raise ValueError(f"Comparator strategy '{comparator_strategy}' not found")
    
    incremental = nmb_df[comparator_strategy] - nmb_df[base_strategy]
    
    return pd.DataFrame({
        'draw': nmb_df.index,
        'incremental_nmb': incremental.values,
        'base': base_strategy,
        'comparator': comparator_strategy
    })


def calculate_nmb_summary(nmb_result: NMBResult) -> pd.DataFrame:
    """
    Calculate summary statistics for NMB results.
    
    Args:
        nmb_result: NMBResult object
    
    Returns:
        DataFrame with summary statistics
    """
    summary_rows = []
    
    for lam in nmb_result.expected.index:
        for strategy in nmb_result.expected.columns:
            # Get NMB values for this lambda and strategy
            nmb_values = nmb_result.nmb_cube.loc[lam, strategy]
            
            summary_rows.append({
                'lambda': lam,
                'strategy': strategy,
                'mean_nmb': nmb_values.mean(),
                'median_nmb': nmb_values.median(),
                'sd_nmb': nmb_values.std(),
                'q025_nmb': nmb_values.quantile(0.025),
                'q975_nmb': nmb_values.quantile(0.975)
            })
    
    return pd.DataFrame(summary_rows)
