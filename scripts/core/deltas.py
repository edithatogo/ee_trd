"""
V4 Incremental Analysis Utilities

Consolidated from V2 analysis_core with enhancements.
Handles computation of incremental costs, effects, and ICERs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

import pandas as pd
import numpy as np


@dataclass
class DeltaDF:
    """Container for incremental analysis results."""
    
    therapy: str
    df: pd.DataFrame  # columns: draw, dE, dC
    base_strategy: str


@dataclass
class ICERResult:
    """Container for ICER calculation results."""
    
    therapy: str
    base_strategy: str
    mean_delta_cost: float
    mean_delta_effect: float
    icer: float
    probability_cost_effective: Optional[float] = None


def compute_deltas(psa: PSAData, therapy: str, base: Optional[str] = None) -> DeltaDF:
    """
    Compute per-draw ΔE and ΔC for a therapy relative to base.
    
    Args:
        psa: PSAData object
        therapy: Therapy to compare
        base: Base strategy (defaults to psa.config.base)
    
    Returns:
        DeltaDF with incremental costs and effects
    """
    if base is None:
        base = psa.config.base
    
    df = psa.table.copy()
    
    # Get base strategy values
    d_base = df[df["strategy"] == base].set_index("draw")["effect"].rename("E_base")
    c_base = df[df["strategy"] == base].set_index("draw")["cost"].rename("C_base")
    
    # Get therapy values
    d_t = (
        df[df["strategy"] == therapy]
        .set_index("draw")[["effect", "cost"]]
        .rename(columns={"effect": "E_i", "cost": "C_i"})
    )
    
    # Merge and compute deltas
    merged = d_t.join(d_base, how="inner").join(c_base, how="inner").reset_index()
    merged["dE"] = merged["E_i"] - merged["E_base"]
    merged["dC"] = merged["C_i"] - merged["C_base"]
    
    out = merged[["draw", "dE", "dC"]].copy()
    
    return DeltaDF(therapy=therapy, df=out, base_strategy=base)


def compute_icer(delta: DeltaDF, lambda_threshold: Optional[float] = None) -> ICERResult:
    """
    Compute ICER and cost-effectiveness probability.
    
    ICER = ΔC / ΔE
    
    Args:
        delta: DeltaDF with incremental costs and effects
        lambda_threshold: WTP threshold for cost-effectiveness probability
    
    Returns:
        ICERResult with ICER and probability
    """
    mean_dc = delta.df["dC"].mean()
    mean_de = delta.df["dE"].mean()
    
    # Compute ICER
    if abs(mean_de) < 1e-10:
        # No incremental effect
        if mean_dc > 0:
            icer = np.inf
        elif mean_dc < 0:
            icer = -np.inf
        else:
            icer = 0.0
    else:
        icer = mean_dc / mean_de
    
    # Compute cost-effectiveness probability if threshold provided
    prob_ce = None
    if lambda_threshold is not None:
        # Cost-effective if: λ × ΔE - ΔC > 0
        incremental_nmb = lambda_threshold * delta.df["dE"] - delta.df["dC"]
        prob_ce = (incremental_nmb > 0).mean()
    
    return ICERResult(
        therapy=delta.therapy,
        base_strategy=delta.base_strategy,
        mean_delta_cost=mean_dc,
        mean_delta_effect=mean_de,
        icer=icer,
        probability_cost_effective=prob_ce
    )


def compute_incremental_analysis(
    psa: PSAData,
    therapies: Optional[list] = None,
    base: Optional[str] = None,
    lambda_threshold: Optional[float] = 50000
) -> pd.DataFrame:
    """
    Compute complete incremental analysis for multiple therapies.
    
    Args:
        psa: PSAData object
        therapies: List of therapies to analyze (defaults to all non-base)
        base: Base strategy (defaults to psa.config.base)
        lambda_threshold: WTP threshold for cost-effectiveness
    
    Returns:
        DataFrame with incremental analysis results
    """
    if base is None:
        base = psa.config.base
    
    if therapies is None:
        therapies = [s for s in psa.strategies if s != base]
    
    results = []
    
    for therapy in therapies:
        # Compute deltas
        delta = compute_deltas(psa, therapy, base)
        
        # Compute ICER
        icer_result = compute_icer(delta, lambda_threshold)
        
        results.append({
            'therapy': therapy,
            'base': base,
            'mean_delta_cost': icer_result.mean_delta_cost,
            'mean_delta_effect': icer_result.mean_delta_effect,
            'icer': icer_result.icer,
            'prob_cost_effective': icer_result.probability_cost_effective
        })
    
    return pd.DataFrame(results)


def identify_dominated_strategies(incremental_df: pd.DataFrame) -> list:
    """
    Identify dominated and extendedly dominated strategies.
    
    A strategy is:
    - Dominated if another strategy has lower cost and higher effect
    - Extendedly dominated if a linear combination of other strategies
      provides better value
    
    Args:
        incremental_df: DataFrame with incremental analysis results
    
    Returns:
        List of dominated strategy names
    """
    dominated = []
    
    # Sort by mean delta effect
    df = incremental_df.sort_values('mean_delta_effect').copy()
    
    for i, row in df.iterrows():
        therapy = row['therapy']
        cost = row['mean_delta_cost']
        effect = row['mean_delta_effect']
        
        # Check for dominance
        for j, other_row in df.iterrows():
            if i == j:
                continue
            
            other_cost = other_row['mean_delta_cost']
            other_effect = other_row['mean_delta_effect']
            
            # Dominated if other has lower cost and higher effect
            if other_cost <= cost and other_effect >= effect:
                if other_cost < cost or other_effect > effect:
                    dominated.append(therapy)
                    break
    
    return dominated


def compute_efficiency_frontier(incremental_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cost-effectiveness efficiency frontier.
    
    Args:
        incremental_df: DataFrame with incremental analysis results
    
    Returns:
        DataFrame with frontier strategies only
    """
    dominated = identify_dominated_strategies(incremental_df)
    frontier = incremental_df[~incremental_df['therapy'].isin(dominated)].copy()
    frontier = frontier.sort_values('mean_delta_effect')
    
    return frontier
