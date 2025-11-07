"""
V4 Cost-Utility Analysis Engine

Consolidated and enhanced CEA implementation from V2 with V3 improvements.
Handles deterministic and probabilistic cost-utility analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from analysis.core.io import PSAData
from analysis.core.nmb import compute_nmb, argmax_with_tiebreak
from analysis.core.deltas import compute_incremental_analysis, compute_efficiency_frontier


@dataclass
class CEAResult:
    """Container for CEA results."""
    
    deterministic: pd.DataFrame  # Deterministic CEA results
    incremental: pd.DataFrame    # Incremental analysis
    frontier: pd.DataFrame       # Efficiency frontier
    perspective: str
    jurisdiction: Optional[str]


@dataclass
class CEACResult:
    """Container for CEAC (Cost-Effectiveness Acceptability Curve) results."""
    
    ceac: pd.DataFrame          # CEAC probabilities for all strategies
    lambda_grid: np.ndarray     # WTP threshold grid
    perspective: str
    jurisdiction: Optional[str]


@dataclass
class CEAFResult:
    """Container for CEAF (Cost-Effectiveness Acceptability Frontier) results."""
    
    ceaf: pd.DataFrame          # CEAF results
    ceac: pd.DataFrame          # Full CEAC for reference
    lambda_grid: np.ndarray     # WTP threshold grid
    perspective: str
    jurisdiction: Optional[str]


def run_deterministic_cea(
    psa: PSAData,
    lambda_threshold: float = 50000
) -> CEAResult:
    """
    Run deterministic cost-utility analysis.
    
    Uses mean costs and effects across PSA draws.
    
    Args:
        psa: PSAData object
        lambda_threshold: WTP threshold for cost-effectiveness
    
    Returns:
        CEAResult with deterministic analysis
    """
    # Compute mean costs and effects
    mean_results = psa.table.groupby('strategy').agg({
        'cost': 'mean',
        'effect': 'mean'
    }).reset_index()
    
    # Compute NMB at threshold
    mean_results['nmb'] = lambda_threshold * mean_results['effect'] - mean_results['cost']
    
    # Compute incremental analysis
    incremental = compute_incremental_analysis(psa, lambda_threshold=lambda_threshold)
    
    # Compute efficiency frontier
    frontier = compute_efficiency_frontier(incremental)
    
    return CEAResult(
        deterministic=mean_results,
        incremental=incremental,
        frontier=frontier,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )


def compute_ceac(
    psa: PSAData,
    lambda_grid: np.ndarray,
    focal: Optional[str] = None
) -> CEACResult:
    """
    Compute Cost-Effectiveness Acceptability Curves.

    CEAC shows the probability that each strategy is optimal
    across a range of WTP thresholds.

    Args:
        psa: PSAData object
        lambda_grid: Array of WTP threshold values
        focal: Optional focal strategy for tie-breaking

    Returns:
        CEACResult with CEAC probabilities
    """
    strategies = psa.strategies

    # Pivot data for vectorized computation
    cost = psa.table.pivot(index="draw", columns="strategy", values="cost")[strategies]
    effect = psa.table.pivot(index="draw", columns="strategy", values="effect")[strategies]

    ceac_rows = []

    for lam in lambda_grid:
        # Compute NMB for this lambda
        nmb = lam * effect - cost

        # Find optimal strategy per draw
        optimal_draws = argmax_with_tiebreak(nmb, focal=focal)

        # Compute probabilities - ensure all strategies are included
        probabilities = optimal_draws.value_counts(normalize=True).reindex(
            strategies, fill_value=0.0
        )

        # Expected NMB
        expected_nmb = nmb.mean(axis=0)

        for strategy in strategies:
            ceac_rows.append({
                'lambda': float(lam),
                'strategy': strategy,
                'probability_optimal': float(probabilities.loc[strategy]),
                'expected_nmb': float(expected_nmb.loc[strategy])
            })

    ceac_df = pd.DataFrame(ceac_rows)

    return CEACResult(
        ceac=ceac_df,
        lambda_grid=lambda_grid,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )


def compute_ceaf(
    psa: PSAData,
    lambda_grid: np.ndarray,
    focal: Optional[str] = None
) -> CEAFResult:
    """
    Compute Cost-Effectiveness Acceptability Frontier.
    
    CEAF identifies the strategy with highest expected NMB
    at each WTP threshold.
    
    Args:
        psa: PSAData object
        lambda_grid: Array of WTP threshold values
        focal: Optional focal strategy for tie-breaking
    
    Returns:
        CEAFResult with CEAF and CEAC
    """
    # First compute full CEAC
    ceac_result = compute_ceac(psa, lambda_grid, focal)
    
    strategies = psa.strategies
    
    # Pivot data
    cost = psa.table.pivot(index="draw", columns="strategy", values="cost")[strategies]
    effect = psa.table.pivot(index="draw", columns="strategy", values="effect")[strategies]
    
    ceaf_rows = []
    
    for lam in lambda_grid:
        # Compute NMB
        nmb = lam * effect - cost
        expected = nmb.mean(axis=0)
        
        # Find optimal strategy per draw
        optimal_draws = argmax_with_tiebreak(nmb, focal=focal)
        probabilities = optimal_draws.value_counts(normalize=True).reindex(
            strategies, fill_value=0.0
        )
        
        # Choose CEAF strategy (highest expected NMB with tie-breaking)
        ceaf_strategy = _choose_expected_optimal(expected, strategies, focal)
        ceaf_probability = float(probabilities.loc[ceaf_strategy])
        ceaf_expected_nmb = float(expected.loc[ceaf_strategy])
        
        ceaf_rows.append({
            'lambda': float(lam),
            'ceaf_strategy': ceaf_strategy,
            'ceaf_probability': ceaf_probability,
            'ceaf_expected_nmb': ceaf_expected_nmb
        })
    
    ceaf_df = pd.DataFrame(ceaf_rows)
    
    return CEAFResult(
        ceaf=ceaf_df,
        ceac=ceac_result.ceac,
        lambda_grid=lambda_grid,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )


def _choose_expected_optimal(
    expected_nmb: pd.Series,
    strategies_order: List[str],
    focal: Optional[str] = None
) -> str:
    """
    Choose expected-optimal strategy with tie-breaking.
    
    Args:
        expected_nmb: Expected NMB for each strategy
        strategies_order: Ordered list of strategies
        focal: Optional focal strategy for tie-breaking
    
    Returns:
        Name of expected-optimal strategy
    """
    max_value = expected_nmb.max()
    candidates = [
        s for s in strategies_order 
        if np.isclose(expected_nmb.get(s, -np.inf), max_value)
    ]
    
    if not candidates:
        raise RuntimeError("Unable to determine expected-optimal strategy")
    
    if focal and focal in candidates:
        return focal
    
    return candidates[0]


def run_complete_cea(
    psa: PSAData,
    lambda_grid: np.ndarray,
    lambda_threshold: float = 50000,
    focal: Optional[str] = None
) -> Tuple[CEAResult, CEACResult, CEAFResult]:
    """
    Run complete cost-utility analysis including deterministic, CEAC, and CEAF.
    
    Args:
        psa: PSAData object
        lambda_grid: Array of WTP threshold values
        lambda_threshold: Single WTP threshold for deterministic analysis
        focal: Optional focal strategy for tie-breaking
    
    Returns:
        Tuple of (CEAResult, CEACResult, CEAFResult)
    """
    # Deterministic CEA
    cea_result = run_deterministic_cea(psa, lambda_threshold)
    
    # CEAC
    ceac_result = compute_ceac(psa, lambda_grid, focal)
    
    # CEAF
    ceaf_result = compute_ceaf(psa, lambda_grid, focal)
    
    return cea_result, ceac_result, ceaf_result


def save_cea_results(
    cea_result: CEAResult,
    ceac_result: CEACResult,
    ceaf_result: CEAFResult,
    output_dir: Path
) -> None:
    """
    Save CEA results to files.
    
    Args:
        cea_result: CEA results
        ceac_result: CEAC results
        ceaf_result: CEAF results
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save deterministic results
    cea_result.deterministic.to_csv(
        output_dir / "cea_deterministic.csv", index=False
    )
    
    # Save incremental analysis
    cea_result.incremental.to_csv(
        output_dir / "cea_incremental.csv", index=False
    )
    
    # Save efficiency frontier
    cea_result.frontier.to_csv(
        output_dir / "cea_frontier.csv", index=False
    )
    
    # Save CEAC
    ceac_result.ceac.to_csv(
        output_dir / "ceac.csv", index=False
    )
    
    # Save CEAF
    ceaf_result.ceaf.to_csv(
        output_dir / "ceaf.csv", index=False
    )
    
    # Save metadata
    metadata = {
        'perspective': cea_result.perspective,
        'jurisdiction': cea_result.jurisdiction,
        'lambda_min': float(ceac_result.lambda_grid.min()),
        'lambda_max': float(ceac_result.lambda_grid.max()),
        'n_strategies': len(cea_result.deterministic),
        'n_draws': len(set(ceac_result.ceac['lambda']))
    }
    
    import json
    with open(output_dir / "cea_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)


def build_lambda_grid(lambda_min: float, lambda_max: float, lambda_step: float) -> np.ndarray:
    """
    Build WTP threshold grid.
    
    Args:
        lambda_min: Minimum WTP threshold
        lambda_max: Maximum WTP threshold
        lambda_step: Step size
    
    Returns:
        Array of WTP thresholds
    """
    if lambda_step <= 0:
        raise ValueError("lambda_step must be positive")
    
    if lambda_max < lambda_min:
        raise ValueError("lambda_max must be >= lambda_min")
    
    n_steps = int(np.floor((lambda_max - lambda_min) / lambda_step + 1e-9))
    grid = lambda_min + lambda_step * np.arange(n_steps + 1)
    
    if grid.size == 0 or grid[-1] < lambda_max:
        grid = np.append(grid, lambda_max)
    
    return np.round(grid, 8)


def compute_inmb_distributions(
    psa: PSAData,
    lambda_threshold: float = 50000,
    base_strategy: Optional[str] = None
) -> pd.DataFrame:
    """
    Compute incremental NMB distributions for all strategies vs baseline.
    
    Args:
        psa: PSAData object
        lambda_threshold: WTP threshold for NMB calculation
        base_strategy: Baseline strategy (defaults to psa.config.base)
    
    Returns:
        DataFrame with INMB distributions (columns: draw, strategy, inmb)
    """
    if base_strategy is None:
        base_strategy = psa.config.base
    
    # Compute NMB for all strategies at the given threshold
    nmb_result = compute_nmb(psa.table, [lambda_threshold])
    
    # Get NMB values for the threshold
    nmb_values = nmb_result.nmb_cube.loc[lambda_threshold]
    
    # Compute incremental NMB vs baseline
    base_nmb = nmb_values[base_strategy]
    
    inmb_rows = []
    for strategy in psa.strategies:
        if strategy == base_strategy:
            continue  # Skip baseline strategy
        
        incremental_nmb = nmb_values[strategy] - base_nmb
        
        # Create rows for each draw
        for draw_idx in incremental_nmb.index:
            inmb_rows.append({
                'draw': draw_idx,
                'strategy': strategy,
                'inmb': incremental_nmb.loc[draw_idx]
            })
    
    return pd.DataFrame(inmb_rows)
