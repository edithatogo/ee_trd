"""
V4 Value-Based Pricing Engine

Implements VBP curves, threshold pricing, and price-probability analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict

import numpy as np
import pandas as pd

from trd_cea.core.io import PSAData


@dataclass
class VBPResult:
    """Container for Value-Based Pricing results."""
    
    vbp_curves: pd.DataFrame        # VBP recommendations across WTP
    threshold_prices: pd.DataFrame  # Maximum cost-effective prices
    price_probability: pd.DataFrame # CE probability at different prices
    perspective: str
    jurisdiction: Optional[str]


def calculate_threshold_price(
    psa: PSAData,
    therapy: str,
    lambda_threshold: float,
    base_strategy: Optional[str] = None
) -> float:
    """
    Calculate maximum price at which therapy is cost-effective.
    
    At threshold price: λ × ΔE = ΔC
    Therefore: Price_threshold = λ × ΔE - ΔC_other
    
    Args:
        psa: PSAData object
        therapy: Therapy to price
        lambda_threshold: WTP threshold
        base_strategy: Base comparator (defaults to psa.config.base)
    
    Returns:
        Threshold price
    """
    if base_strategy is None:
        base_strategy = psa.config.base
    
    # Get mean effects and costs
    therapy_data = psa.table[psa.table['strategy'] == therapy]
    base_data = psa.table[psa.table['strategy'] == base_strategy]
    
    mean_effect_therapy = therapy_data['effect'].mean()
    mean_effect_base = base_data['effect'].mean()
    mean_cost_therapy = therapy_data['cost'].mean()
    mean_cost_base = base_data['cost'].mean()
    
    # Incremental effect
    delta_effect = mean_effect_therapy - mean_effect_base
    
    # Incremental cost excluding therapy price
    delta_cost_other = mean_cost_therapy - mean_cost_base
    
    # Threshold price
    threshold_price = lambda_threshold * delta_effect - delta_cost_other
    
    return float(max(0, threshold_price))


def calculate_vbp_curve(
    psa: PSAData,
    therapy: str,
    lambda_grid: np.ndarray,
    base_strategy: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate VBP curve across WTP thresholds.
    
    Args:
        psa: PSAData object
        therapy: Therapy to price
        lambda_grid: Array of WTP thresholds
        base_strategy: Base comparator
    
    Returns:
        DataFrame with VBP recommendations including CE probabilities
    """
    if base_strategy is None:
        base_strategy = psa.config.base

    therapy_data = psa.table[psa.table['strategy'] == therapy].set_index('draw')
    base_data = psa.table[psa.table['strategy'] == base_strategy].set_index('draw')

    # Align draws to avoid mismatched comparisons
    common_draws = therapy_data.index.intersection(base_data.index)
    therapy_data = therapy_data.loc[common_draws]
    base_data = base_data.loc[common_draws]

    vbp_rows: List[Dict[str, float]] = []
    
    for lam in lambda_grid:
        threshold_price = calculate_threshold_price(
            psa, therapy, lam, base_strategy
        )

        # Probability therapy is cost-effective versus the base strategy
        therapy_nmb = lam * therapy_data['effect'] - therapy_data['cost']
        base_nmb = lam * base_data['effect'] - base_data['cost']
        prob_ce = float((therapy_nmb > base_nmb).mean())
        
        vbp_rows.append({
            'therapy': therapy,
            'lambda': float(lam),
            'threshold_price': threshold_price,
            'probability_ce': prob_ce,
            'base_strategy': base_strategy
        })
    
    return pd.DataFrame(vbp_rows)


def calculate_vbp_curves(
    psa: PSAData,
    lambda_grid: np.ndarray,
    base_strategy: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate VBP curves for all therapies.
    
    Args:
        psa: PSAData object
        lambda_grid: Array of WTP thresholds
        base_strategy: Base comparator
    
    Returns:
        DataFrame with VBP recommendations for all therapies
    """
    base_strategy = base_strategy or psa.config.base
    all_vbp_rows: List[Dict[str, float]] = []
    
    for therapy in psa.strategies:
        if therapy == base_strategy:
            continue  # Skip base strategy
        
        vbp_curve = calculate_vbp_curve(psa, therapy, lambda_grid, base_strategy)
        all_vbp_rows.extend(vbp_curve.to_dict('records'))
    
    return pd.DataFrame(all_vbp_rows)


def calculate_threshold_prices(
    psa: PSAData,
    lambda_grid: np.ndarray,
    base_strategy: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate threshold prices for all therapies across lambda grid.
    
    Args:
        psa: PSAData object
        lambda_grid: Array of WTP thresholds
        base_strategy: Base comparator
    
    Returns:
        DataFrame with threshold prices for all therapies
    """
    threshold_rows = []
    
    for therapy in psa.strategies:
        if therapy == (base_strategy or psa.config.base):
            continue  # Skip base strategy
        
        for lam in lambda_grid:
            threshold_price = calculate_threshold_price(
                psa, therapy, lam, base_strategy
            )
            
            threshold_rows.append({
                'therapy': therapy,
                'lambda': float(lam),
                'wtp_threshold': float(lam),
                'threshold_price': threshold_price,
                'base_strategy': base_strategy or psa.config.base
            })
    
    return pd.DataFrame(threshold_rows)


def calculate_price_probability(
    psa: PSAData,
    therapy: str,
    price_grid: np.ndarray,
    lambda_threshold: float,
    base_strategy: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate probability of cost-effectiveness at different prices.
    
    Args:
        psa: PSAData object
        therapy: Therapy to analyze
        price_grid: Array of price points
        lambda_threshold: WTP threshold
        base_strategy: Base comparator
    
    Returns:
        DataFrame with CE probabilities at each price
    """
    if base_strategy is None:
        base_strategy = psa.config.base
    
    # Get data for therapy and base
    therapy_data = psa.table[psa.table['strategy'] == therapy].set_index('draw')
    base_data = psa.table[psa.table['strategy'] == base_strategy].set_index('draw')
    
    # Align draws
    common_draws = therapy_data.index.intersection(base_data.index)
    therapy_data = therapy_data.loc[common_draws]
    base_data = base_data.loc[common_draws]
    
    prob_rows = []
    
    for price in price_grid:
        # Adjust therapy cost by price
        adjusted_cost = therapy_data['cost'] + price
        
        # Calculate incremental NMB
        delta_effect = therapy_data['effect'] - base_data['effect']
        delta_cost = adjusted_cost - base_data['cost']
        incremental_nmb = lambda_threshold * delta_effect - delta_cost
        
        # Probability cost-effective
        prob_ce = (incremental_nmb > 0).mean()
        
        prob_rows.append({
            'therapy': therapy,
            'price': float(price),
            'lambda': float(lambda_threshold),
            'probability_ce': float(prob_ce)
        })
    
    return pd.DataFrame(prob_rows)


def calculate_price_elasticity(
    psa: PSAData,
    price_range: np.ndarray,
    lambda_threshold: float = 50000,
    base_strategy: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate price elasticity of demand for therapies.
    
    Args:
        psa: PSAData object
        price_range: Array of prices to test
        lambda_threshold: WTP threshold
        base_strategy: Base comparator
    
    Returns:
        DataFrame with price elasticity data
    """
    if base_strategy is None:
        base_strategy = psa.config.base
    
    elasticity_rows = []
    
    for therapy in psa.strategies:
        if therapy == base_strategy:
            continue
        
        # Get data for this therapy and base
        therapy_data = psa.table[psa.table['strategy'] == therapy].copy()
        _base_data = psa.table[psa.table['strategy'] == base_strategy].copy()
        
        # Ensure we have the same draws for comparison
        common_draws = set(therapy_data['draw']) & set(_base_data['draw'])
        therapy_data = therapy_data[therapy_data['draw'].isin(common_draws)]
        # Ensure _base_data is filtered to common draws (correct indexing)
        _base_data = _base_data[_base_data['draw'].isin(common_draws)]
        
        for price in price_range:
            # Calculate NMB at this price
            adjusted_cost = therapy_data['cost'] + price
            therapy_nmb = lambda_threshold * therapy_data['effect'] - adjusted_cost
            base_nmb = lambda_threshold * _base_data['effect'] - _base_data['cost']
            
            # Probability therapy is cost-effective
            prob_ce = (therapy_nmb.values > base_nmb.values).mean()
            
            elasticity_rows.append({
                'therapy': therapy,
                'price': float(price),
                'probability_ce': float(prob_ce),
                'lambda': lambda_threshold
            })
    
    return pd.DataFrame(elasticity_rows)


def calculate_risk_sharing_scenarios(psa: PSAData) -> pd.DataFrame:
    """
    Calculate risk-sharing scenarios for therapies.
    
    Args:
        psa: PSAData object
    
    Returns:
        DataFrame with risk-sharing scenario data
    """
    # Simplified risk-sharing implementation
    scenarios = []
    
    for therapy in psa.strategies:
        if therapy == psa.config.base:
            continue
        
        therapy_data = psa.table[psa.table['strategy'] == therapy]
        _base_data = psa.table[psa.table['strategy'] == psa.config.base]
        
        # Calculate basic risk metrics
        therapy_cost_var = therapy_data['cost'].var()
        therapy_effect_var = therapy_data['effect'].var()
        
        # Simple risk-sharing scenarios
        scenarios.extend([
            {
                'therapy': therapy,
                'scenario': 'cost_cap',
                'risk_metric': 'cost_variance',
                'value': float(therapy_cost_var),
                'description': 'Cost cap at 95th percentile'
            },
            {
                'therapy': therapy,
                'scenario': 'outcome_guarantee',
                'risk_metric': 'effect_variance',
                'value': float(therapy_effect_var),
                'description': 'Outcome guarantee for minimum effect'
            },
            {
                'therapy': therapy,
                'scenario': 'blended_payment',
                'risk_metric': 'combined_risk',
                'value': float(therapy_cost_var + therapy_effect_var),
                'description': 'Blended payment model'
            }
        ])
    
    return pd.DataFrame(scenarios)


def run_vbp_analysis(
    psa: PSAData,
    therapies: Optional[List[str]] = None,
    lambda_grid: Optional[np.ndarray] = None,
    price_grid: Optional[np.ndarray] = None,
    lambda_threshold: float = 50000,
    base_strategy: Optional[str] = None
) -> VBPResult:
    """
    Run complete Value-Based Pricing analysis.
    
    Args:
        psa: PSAData object
        therapies: List of therapies to analyze (defaults to all non-base)
        lambda_grid: WTP threshold grid for VBP curves
        price_grid: Price grid for price-probability analysis
        lambda_threshold: Single WTP threshold for price-probability
        base_strategy: Base comparator
    
    Returns:
        VBPResult with complete pricing analysis
    """
    if base_strategy is None:
        base_strategy = psa.config.base
    
    if therapies is None:
        therapies = [s for s in psa.strategies if s != base_strategy]
    
    if lambda_grid is None:
        lambda_grid = np.arange(0, 75001, 5000)
    
    if price_grid is None:
        price_grid = np.arange(0, 50001, 1000)
    
    # Calculate VBP curves
    vbp_curves_list = []
    for therapy in therapies:
        vbp_curve = calculate_vbp_curve(psa, therapy, lambda_grid, base_strategy)
        vbp_curves_list.append(vbp_curve)
    
    vbp_curves = pd.concat(vbp_curves_list, ignore_index=True)
    
    # Calculate threshold prices at standard WTP
    threshold_rows = []
    for therapy in therapies:
        threshold_price = calculate_threshold_price(
            psa, therapy, lambda_threshold, base_strategy
        )
        threshold_rows.append({
            'therapy': therapy,
            'lambda': lambda_threshold,
            'threshold_price': threshold_price
        })
    
    threshold_prices = pd.DataFrame(threshold_rows)
    
    # Calculate price-probability curves
    price_prob_list = []
    for therapy in therapies:
        price_prob = calculate_price_probability(
            psa, therapy, price_grid, lambda_threshold, base_strategy
        )
        price_prob_list.append(price_prob)
    
    price_probability = pd.concat(price_prob_list, ignore_index=True)
    
    return VBPResult(
        vbp_curves=vbp_curves,
        threshold_prices=threshold_prices,
        price_probability=price_probability,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )


def save_vbp_results(
    vbp_result: VBPResult,
    output_dir: Path
) -> None:
    """
    Save VBP results to files.
    
    Args:
        vbp_result: VBP results
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save VBP curves
    vbp_result.vbp_curves.to_csv(output_dir / "vbp_curves.csv", index=False)
    
    # Save threshold prices
    vbp_result.threshold_prices.to_csv(
        output_dir / "threshold_prices.csv", index=False
    )
    
    # Save price-probability
    vbp_result.price_probability.to_csv(
        output_dir / "price_probability.csv", index=False
    )
    
    # Save metadata
    import json
    metadata = {
        'perspective': vbp_result.perspective,
        'jurisdiction': vbp_result.jurisdiction,
        'n_therapies': len(vbp_result.threshold_prices)
    }
    
    with open(output_dir / "vbp_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
