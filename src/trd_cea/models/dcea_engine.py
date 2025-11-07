"""
V4 Distributional Cost-Effectiveness Analysis Engine

Implements DCEA with social welfare functions, equity analysis, and Indigenous population considerations.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

import numpy as np
import pandas as pd

from trd_cea.core.io import PSAData


@dataclass
class DCEAResult:
    """Container for DCEA results."""
    
    ede_qalys: pd.DataFrame          # Equally Distributed Equivalent QALYs
    atkinson_index: pd.DataFrame     # Atkinson inequality index
    distributional_ceac: pd.DataFrame # Equity-weighted CEAC
    equity_impact: pd.DataFrame      # Efficiency vs equity trade-offs
    perspective: str
    jurisdiction: Optional[str]
    epsilon: float                   # Inequality aversion parameter


@dataclass
class IndigenousDCEAResult:
    """Container for Indigenous population DCEA results."""
    
    population: str                  # Aboriginal, Māori, or Pacific Islander
    ede_qalys: pd.DataFrame
    atkinson_index: pd.DataFrame
    equity_metrics: pd.DataFrame
    perspective: str
    jurisdiction: Optional[str]


def calculate_atkinson_index(
    qalys: np.ndarray,
    weights: Optional[np.ndarray] = None,
    epsilon: float = 1.5
) -> float:
    """
    Calculate Atkinson inequality index.
    
    A = 1 - (Σwᵢ × QALYᵢ^(1-ε))^(1/(1-ε)) / μ
    
    Args:
        qalys: Array of QALY values
        weights: Optional population weights (defaults to equal)
        epsilon: Inequality aversion parameter (0 = no aversion, higher = more aversion)
    
    Returns:
        Atkinson index (0 = perfect equality, 1 = maximum inequality)
    """
    if weights is None:
        weights = np.ones(len(qalys)) / len(qalys)
    
    # Normalize weights
    weights = weights / weights.sum()
    
    # Mean QALYs
    mean_qalys = np.average(qalys, weights=weights)
    
    if mean_qalys <= 0:
        return np.nan
    
    if epsilon == 1:
        # Special case: geometric mean
        log_qalys = np.log(np.maximum(qalys, 1e-10))
        ede = np.exp(np.average(log_qalys, weights=weights))
    else:
        # General case
        powered = np.power(np.maximum(qalys, 1e-10), 1 - epsilon)
        weighted_sum = np.average(powered, weights=weights)
        ede = np.power(weighted_sum, 1 / (1 - epsilon))
    
    atkinson = 1 - (ede / mean_qalys)
    
    return float(np.clip(atkinson, 0, 1))


def calculate_ede_qalys(
    qalys: np.ndarray,
    weights: Optional[np.ndarray] = None,
    epsilon: float = 1.5
) -> float:
    """
    Calculate Equally Distributed Equivalent QALYs.
    
    EDE = (Σwᵢ × QALYᵢ^(1-ε))^(1/(1-ε))
    
    Args:
        qalys: Array of QALY values
        weights: Optional population weights
        epsilon: Inequality aversion parameter
    
    Returns:
        EDE-QALYs value
    """
    if weights is None:
        weights = np.ones(len(qalys)) / len(qalys)
    
    weights = weights / weights.sum()
    
    if epsilon == 1:
        log_qalys = np.log(np.maximum(qalys, 1e-10))
        ede = np.exp(np.average(log_qalys, weights=weights))
    else:
        powered = np.power(np.maximum(qalys, 1e-10), 1 - epsilon)
        weighted_sum = np.average(powered, weights=weights)
        ede = np.power(weighted_sum, 1 / (1 - epsilon))
    
    return float(ede)


def social_welfare_function(
    qalys: np.ndarray,
    weights: Optional[np.ndarray] = None,
    epsilon: float = 1.5
) -> float:
    """
    Calculate social welfare with inequality aversion.
    
    W = Σwᵢ × u(QALYᵢ) where u(x) = x^(1-ε)/(1-ε)
    
    Args:
        qalys: Array of QALY values
        weights: Optional population weights
        epsilon: Inequality aversion parameter
    
    Returns:
        Social welfare value
    """
    if weights is None:
        weights = np.ones(len(qalys)) / len(qalys)
    
    weights = weights / weights.sum()
    
    if epsilon == 1:
        # Logarithmic utility
        utility = np.log(np.maximum(qalys, 1e-10))
    else:
        # Power utility
        utility = np.power(np.maximum(qalys, 1e-10), 1 - epsilon) / (1 - epsilon)
    
    welfare = np.average(utility, weights=weights)
    
    return float(welfare)


def run_dcea(
    psa: PSAData,
    epsilon: float = 1.5,
    subgroup_weights: Optional[Dict[str, float]] = None
) -> DCEAResult:
    """
    Run Distributional Cost-Effectiveness Analysis.
    
    Args:
        psa: PSAData object
        epsilon: Inequality aversion parameter (default 1.5)
        subgroup_weights: Optional weights for different subgroups
    
    Returns:
        DCEAResult with equity analysis
    """
    strategies = psa.strategies
    
    # Get effects (QALYs) for each strategy
    effects = psa.table.pivot(index="draw", columns="strategy", values="effect")
    
    ede_rows = []
    atkinson_rows = []
    
    for strategy in strategies:
        strategy_qalys = effects[strategy].values
        
        # Calculate EDE-QALYs
        ede = calculate_ede_qalys(strategy_qalys, epsilon=epsilon)
        
        # Calculate Atkinson index
        atkinson = calculate_atkinson_index(strategy_qalys, epsilon=epsilon)
        
        # Calculate social welfare
        welfare = social_welfare_function(strategy_qalys, epsilon=epsilon)
        
        ede_rows.append({
            'strategy': strategy,
            'mean_qalys': strategy_qalys.mean(),
            'ede_qalys': ede,
            'social_welfare': welfare,
            'epsilon': epsilon
        })
        
        atkinson_rows.append({
            'strategy': strategy,
            'atkinson_index': atkinson,
            'epsilon': epsilon
        })
    
    ede_df = pd.DataFrame(ede_rows)
    atkinson_df = pd.DataFrame(atkinson_rows)
    
    # Placeholder for distributional CEAC and equity impact
    # These would require more complex calculations with subgroup data
    distributional_ceac = pd.DataFrame()
    equity_impact = pd.DataFrame()
    
    return DCEAResult(
        ede_qalys=ede_df,
        atkinson_index=atkinson_df,
        distributional_ceac=distributional_ceac,
        equity_impact=equity_impact,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction,
        epsilon=epsilon
    )


def run_indigenous_dcea(
    psa: PSAData,
    population: str,
    epsilon: float = 1.5,
    cultural_weights: Optional[np.ndarray] = None
) -> IndigenousDCEAResult:
    """
    Run DCEA for Indigenous populations.
    
    Args:
        psa: PSAData object
        population: 'Aboriginal', 'Māori', or 'Pacific Islander'
        epsilon: Inequality aversion parameter
        cultural_weights: Optional culturally-adapted weights
    
    Returns:
        IndigenousDCEAResult with population-specific equity analysis
    """
    valid_populations = ['Aboriginal', 'Māori', 'Pacific Islander']
    if population not in valid_populations:
        raise ValueError(f"Population must be one of {valid_populations}")
    
    strategies = psa.strategies
    effects = psa.table.pivot(index="draw", columns="strategy", values="effect")
    
    ede_rows = []
    atkinson_rows = []
    equity_rows = []
    
    for strategy in strategies:
        strategy_qalys = effects[strategy].values
        
        # Calculate with cultural weights if provided
        ede = calculate_ede_qalys(strategy_qalys, weights=cultural_weights, epsilon=epsilon)
        atkinson = calculate_atkinson_index(strategy_qalys, weights=cultural_weights, epsilon=epsilon)
        welfare = social_welfare_function(strategy_qalys, weights=cultural_weights, epsilon=epsilon)
        
        ede_rows.append({
            'population': population,
            'strategy': strategy,
            'mean_qalys': strategy_qalys.mean(),
            'ede_qalys': ede,
            'social_welfare': welfare,
            'epsilon': epsilon
        })
        
        atkinson_rows.append({
            'population': population,
            'strategy': strategy,
            'atkinson_index': atkinson,
            'epsilon': epsilon
        })
        
        # Calculate equity metrics
        equity_rows.append({
            'population': population,
            'strategy': strategy,
            'efficiency': strategy_qalys.mean(),
            'equity': 1 - atkinson,  # Higher is more equitable
            'social_welfare': welfare
        })
    
    return IndigenousDCEAResult(
        population=population,
        ede_qalys=pd.DataFrame(ede_rows),
        atkinson_index=pd.DataFrame(atkinson_rows),
        equity_metrics=pd.DataFrame(equity_rows),
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )


def save_dcea_results(
    dcea_result: DCEAResult,
    output_dir: Path
) -> None:
    """
    Save DCEA results to files.
    
    Args:
        dcea_result: DCEA results
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save EDE-QALYs
    dcea_result.ede_qalys.to_csv(output_dir / "dcea_ede_qalys.csv", index=False)
    
    # Save Atkinson indices
    dcea_result.atkinson_index.to_csv(output_dir / "dcea_atkinson_index.csv", index=False)
    
    # Save distributional CEAC if available
    if not dcea_result.distributional_ceac.empty:
        dcea_result.distributional_ceac.to_csv(
            output_dir / "dcea_distributional_ceac.csv", index=False
        )
    
    # Save equity impact if available
    if not dcea_result.equity_impact.empty:
        dcea_result.equity_impact.to_csv(
            output_dir / "dcea_equity_impact.csv", index=False
        )
    
    # Save metadata
    import json
    metadata = {
        'perspective': dcea_result.perspective,
        'jurisdiction': dcea_result.jurisdiction,
        'epsilon': dcea_result.epsilon,
        'n_strategies': len(dcea_result.ede_qalys)
    }
    
    with open(output_dir / "dcea_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)


def save_indigenous_dcea_results(
    indigenous_result: IndigenousDCEAResult,
    output_dir: Path
) -> None:
    """
    Save Indigenous DCEA results to files.
    
    Args:
        indigenous_result: Indigenous DCEA results
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pop = indigenous_result.population.lower().replace(' ', '_')
    
    # Save results
    indigenous_result.ede_qalys.to_csv(
        output_dir / f"dcea_{pop}_ede_qalys.csv", index=False
    )
    indigenous_result.atkinson_index.to_csv(
        output_dir / f"dcea_{pop}_atkinson_index.csv", index=False
    )
    indigenous_result.equity_metrics.to_csv(
        output_dir / f"dcea_{pop}_equity_metrics.csv", index=False
    )


def calculate_equity_impact(psa: PSAData) -> pd.DataFrame:
    """
    Calculate equity impact plane data.
    
    Args:
        psa: PSA data with strategy information
        
    Returns:
        DataFrame with equity impact data
    """
    strategies = psa.table['strategy'].unique()
    results = []
    
    for strategy in strategies:
        strategy_data = psa.table[psa.table['strategy'] == strategy]
        
        # Calculate efficiency (mean QALYs) vs equity (Atkinson index)
        mean_qalys = strategy_data['effect'].mean()
        atkinson = calculate_atkinson_index(strategy_data['effect'].values)
        
        results.append({
            'strategy': strategy,
            'mean_qalys': mean_qalys,
            'atkinson_index': atkinson,
            'equity_efficiency_ratio': atkinson / mean_qalys if mean_qalys > 0 else 0
        })
    
    return pd.DataFrame(results)


def calculate_atkinson_by_strategy(psa: PSAData) -> pd.DataFrame:
    """
    Calculate Atkinson index by strategy.
    
    Args:
        psa: PSA data with strategy information
        
    Returns:
        DataFrame with Atkinson indices by strategy
    """
    strategies = psa.table['strategy'].unique()
    results = []
    
    for strategy in strategies:
        strategy_data = psa.table[psa.table['strategy'] == strategy]
        atkinson = calculate_atkinson_index(strategy_data['effect'].values)
        
        results.append({
            'strategy': strategy,
            'atkinson_index': atkinson,
            'sample_size': len(strategy_data)
        })
    
    return pd.DataFrame(results)


def calculate_ede_comparison(psa: PSAData) -> pd.DataFrame:
    """
    Calculate EDE-QALYs comparison across strategies.
    
    Args:
        psa: PSA data with strategy information
        
    Returns:
        DataFrame with EDE comparison
    """
    strategies = psa.table['strategy'].unique()
    results = []
    
    for strategy in strategies:
        strategy_data = psa.table[psa.table['strategy'] == strategy]
        ede = calculate_ede_qalys(strategy_data['effect'].values)
        mean_qalys = strategy_data['effect'].mean()
        
        results.append({
            'strategy': strategy,
            'mean_qalys': mean_qalys,
            'ede_qalys': ede,
            'equity_loss': mean_qalys - ede
        })
    
    return pd.DataFrame(results)


def calculate_distributional_ceac(psa: PSAData, lambda_grid: np.ndarray) -> pd.DataFrame:
    """
    Calculate distributional CEAC (Cost-Effectiveness Acceptability Curve).
    
    Args:
        psa: PSA data with strategy information
        lambda_grid: Array of WTP thresholds
        
    Returns:
        DataFrame with distributional CEAC data
    """
    strategies = psa.table['strategy'].unique()
    results = []
    
    for lambda_val in lambda_grid:
        for strategy in strategies:
            strategy_data = psa.table[psa.table['strategy'] == strategy]
            
            # Calculate equity-weighted NMB
            qalys = strategy_data['effect'].values
            costs = strategy_data['cost'].values
            
            # Simple equity weighting (could be more sophisticated)
            ede_qalys = calculate_ede_qalys(qalys)
            equity_weighted_nmb = ede_qalys * lambda_val - costs.mean()
            
            results.append({
                'lambda': lambda_val,
                'strategy': strategy,
                'equity_weighted_nmb': equity_weighted_nmb,
                'probability_optimal': 1.0 if equity_weighted_nmb > 0 else 0.0  # Simplified
            })
    
    return pd.DataFrame(results)


def calculate_subgroup_comparison(psa: PSAData) -> pd.DataFrame:
    """
    Calculate subgroup comparison (by age, severity, etc.).
    
    Args:
        psa: PSA data with strategy information
        
    Returns:
        DataFrame with subgroup comparison
    """
    # Mock subgroup analysis - in practice would use actual subgroup data
    strategies = psa.table['strategy'].unique()
    subgroups = ['young_adults', 'middle_aged', 'older_adults', 'severe_depression', 'moderate_depression']
    results = []
    
    for strategy in strategies:
        for subgroup in subgroups:
            # Mock different outcomes by subgroup
            if subgroup == 'young_adults':
                effect_mult = 1.2
                cost_mult = 0.9
            elif subgroup == 'older_adults':
                effect_mult = 0.8
                cost_mult = 1.1
            elif subgroup == 'severe_depression':
                effect_mult = 0.9
                cost_mult = 1.3
            else:  # moderate_depression or middle_aged
                effect_mult = 1.0
                cost_mult = 1.0
            
            strategy_data = psa.table[psa.table['strategy'] == strategy]
            base_effect = strategy_data['effect'].mean()
            base_cost = strategy_data['cost'].mean()
            
            subgroup_effect = base_effect * effect_mult
            subgroup_cost = base_cost * cost_mult
            
            results.append({
                'strategy': strategy,
                'subgroup': subgroup,
                'effect': subgroup_effect,
                'cost': subgroup_cost,
                'icer': subgroup_cost / subgroup_effect if subgroup_effect != 0 else 0
            })
    
    return pd.DataFrame(results)
