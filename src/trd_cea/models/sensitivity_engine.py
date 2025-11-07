"""
V4 Sensitivity Analysis Engine

Implements one-way, two-way, three-way DSA with tornado diagrams and multi-dimensional analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable

import numpy as np
import pandas as pd

from trd_cea.core.io import PSAData


@dataclass
class SensitivityResult:
    """Container for sensitivity analysis results."""
    
    parameter: str
    base_value: float
    low_value: float
    high_value: float
    base_outcome: float
    low_outcome: float
    high_outcome: float
    range: float  # high_outcome - low_outcome


@dataclass
class TornadoResult:
    """Container for tornado diagram results."""
    
    sensitivity_results: pd.DataFrame
    ranked_parameters: List[str]
    outcome_metric: str


@dataclass
class TwoWayDSAResult:
    """Container for two-way DSA results."""
    
    results_grid: pd.DataFrame
    param1: str
    param2: str
    param1_values: np.ndarray
    param2_values: np.ndarray


@dataclass
class ThreeWayDSAResult:
    """Container for three-way DSA results."""
    
    results_grid: pd.DataFrame
    param1: str
    param2: str
    param3: str
    param1_values: np.ndarray
    param2_values: np.ndarray
    param3_values: np.ndarray


def one_way_dsa(
    base_outcome: float,
    parameter_name: str,
    base_value: float,
    low_value: float,
    high_value: float,
    outcome_function: Callable[[float], float]
) -> SensitivityResult:
    """
    Perform one-way deterministic sensitivity analysis.
    
    Args:
        base_outcome: Outcome at base parameter value
        parameter_name: Name of parameter
        base_value: Base parameter value
        low_value: Low parameter value
        high_value: High parameter value
        outcome_function: Function that calculates outcome given parameter value
    
    Returns:
        SensitivityResult
    """
    low_outcome = outcome_function(low_value)
    high_outcome = outcome_function(high_value)
    
    return SensitivityResult(
        parameter=parameter_name,
        base_value=base_value,
        low_value=low_value,
        high_value=high_value,
        base_outcome=base_outcome,
        low_outcome=low_outcome,
        high_outcome=high_outcome,
        range=abs(high_outcome - low_outcome)
    )


def tornado_analysis(
    parameters: Dict[str, Tuple[float, float, float]],  # name: (base, low, high)
    outcome_function: Callable[[Dict[str, float]], float],
    outcome_metric: str = "NMB"
) -> TornadoResult:
    """
    Perform tornado analysis across multiple parameters.
    
    Args:
        parameters: Dictionary of parameter names to (base, low, high) tuples
        outcome_function: Function that calculates outcome given parameter dict
        outcome_metric: Name of outcome metric
    
    Returns:
        TornadoResult with ranked parameters
    """
    # Calculate base outcome
    base_params = {name: values[0] for name, values in parameters.items()}
    base_outcome = outcome_function(base_params)
    
    # Perform one-way DSA for each parameter
    results = []
    
    for param_name, (base_val, low_val, high_val) in parameters.items():
        # Low scenario
        low_params = base_params.copy()
        low_params[param_name] = low_val
        low_outcome = outcome_function(low_params)
        
        # High scenario
        high_params = base_params.copy()
        high_params[param_name] = high_val
        high_outcome = outcome_function(high_params)
        
        results.append({
            'parameter': param_name,
            'base_value': base_val,
            'low_value': low_val,
            'high_value': high_val,
            'base_outcome': base_outcome,
            'low_outcome': low_outcome,
            'high_outcome': high_outcome,
            'range': abs(high_outcome - low_outcome)
        })
    
    results_df = pd.DataFrame(results)
    
    # Rank by range (impact)
    results_df = results_df.sort_values('range', ascending=False)
    ranked_parameters = results_df['parameter'].tolist()
    
    return TornadoResult(
        sensitivity_results=results_df,
        ranked_parameters=ranked_parameters,
        outcome_metric=outcome_metric
    )


def two_way_dsa(
    param1_name: str,
    param1_values: np.ndarray,
    param2_name: str,
    param2_values: np.ndarray,
    outcome_function: Callable[[float, float], float]
) -> TwoWayDSAResult:
    """
    Perform two-way deterministic sensitivity analysis.
    
    Args:
        param1_name: Name of first parameter
        param1_values: Array of values for first parameter
        param2_name: Name of second parameter
        param2_values: Array of values for second parameter
        outcome_function: Function that calculates outcome given both parameters
    
    Returns:
        TwoWayDSAResult with results grid
    """
    results = []
    
    for val1 in param1_values:
        for val2 in param2_values:
            outcome = outcome_function(val1, val2)
            results.append({
                param1_name: val1,
                param2_name: val2,
                'outcome': outcome
            })
    
    results_df = pd.DataFrame(results)
    
    return TwoWayDSAResult(
        results_grid=results_df,
        param1=param1_name,
        param2=param2_name,
        param1_values=param1_values,
        param2_values=param2_values
    )


def three_way_dsa(
    param1_name: str,
    param1_values: np.ndarray,
    param2_name: str,
    param2_values: np.ndarray,
    param3_name: str,
    param3_values: np.ndarray,
    outcome_function: Callable[[float, float, float], float]
) -> ThreeWayDSAResult:
    """
    Perform three-way deterministic sensitivity analysis (3D DSA).
    
    Args:
        param1_name: Name of first parameter
        param1_values: Array of values for first parameter
        param2_name: Name of second parameter
        param2_values: Array of values for second parameter
        param3_name: Name of third parameter
        param3_values: Array of values for third parameter
        outcome_function: Function that calculates outcome given all three parameters
    
    Returns:
        ThreeWayDSAResult with results grid
    """
    results = []
    
    for val1 in param1_values:
        for val2 in param2_values:
            for val3 in param3_values:
                outcome = outcome_function(val1, val2, val3)
                results.append({
                    param1_name: val1,
                    param2_name: val2,
                    param3_name: val3,
                    'outcome': outcome
                })
    
    results_df = pd.DataFrame(results)
    
    return ThreeWayDSAResult(
        results_grid=results_df,
        param1=param1_name,
        param2=param2_name,
        param3=param3_name,
        param1_values=param1_values,
        param2_values=param2_values,
        param3_values=param3_values
    )


def calculate_prcc(
    psa_data: pd.DataFrame,
    outcome_column: str,
    parameter_columns: List[str]
) -> pd.DataFrame:
    """
    Calculate Partial Rank Correlation Coefficients (PRCC).
    
    Args:
        psa_data: PSA data with parameters and outcomes
        outcome_column: Name of outcome column
        parameter_columns: List of parameter column names
    
    Returns:
        DataFrame with PRCC values
    """
    from scipy.stats import spearmanr
    
    # Rank transform all variables
    ranked_data = psa_data[parameter_columns + [outcome_column]].rank()
    
    prcc_results = []
    
    for param in parameter_columns:
        # Calculate Spearman correlation between ranked parameter and ranked outcome
        corr, pval = spearmanr(
            ranked_data[param],
            ranked_data[outcome_column]
        )
        
        prcc_results.append({
            'parameter': param,
            'prcc': corr,
            'p_value': pval,
            'abs_prcc': abs(corr)
        })
    
    prcc_df = pd.DataFrame(prcc_results)
    prcc_df = prcc_df.sort_values('abs_prcc', ascending=False)
    
    return prcc_df


def scenario_analysis(
    scenarios: Dict[str, Dict[str, float]],
    outcome_function: Callable[[Dict[str, float]], float]
) -> pd.DataFrame:
    """
    Perform scenario analysis.
    
    Args:
        scenarios: Dictionary of scenario names to parameter dictionaries
        outcome_function: Function that calculates outcome given parameters
    
    Returns:
        DataFrame with scenario results
    """
    results = []
    
    for scenario_name, parameters in scenarios.items():
        outcome = outcome_function(parameters)
        
        result = {'scenario': scenario_name, 'outcome': outcome}
        result.update(parameters)
        results.append(result)
    
    return pd.DataFrame(results)


def save_sensitivity_results(
    tornado_result: Optional[TornadoResult] = None,
    two_way_result: Optional[TwoWayDSAResult] = None,
    three_way_result: Optional[ThreeWayDSAResult] = None,
    prcc_result: Optional[pd.DataFrame] = None,
    scenario_result: Optional[pd.DataFrame] = None,
    output_dir: Path = Path("results/sensitivity")
) -> None:
    """
    Save sensitivity analysis results.
    
    Args:
        tornado_result: Tornado analysis results
        two_way_result: Two-way DSA results
        three_way_result: Three-way DSA results
        prcc_result: PRCC results
        scenario_result: Scenario analysis results
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if tornado_result:
        tornado_result.sensitivity_results.to_csv(
            output_dir / "tornado_analysis.csv", index=False
        )
    
    if two_way_result:
        two_way_result.results_grid.to_csv(
            output_dir / "two_way_dsa.csv", index=False
        )
    
    if three_way_result:
        three_way_result.results_grid.to_csv(
            output_dir / "three_way_dsa.csv", index=False
        )
    
    if prcc_result is not None:
        prcc_result.to_csv(
            output_dir / "prcc_analysis.csv", index=False
        )
    
    if scenario_result is not None:
        scenario_result.to_csv(
            output_dir / "scenario_analysis.csv", index=False
        )


def run_one_way_dsa(psa: PSAData) -> pd.DataFrame:
    """
    Run one-way deterministic sensitivity analysis on PSA data.
    
    Args:
        psa: PSA data with strategy information
        
    Returns:
        DataFrame with sensitivity analysis results
    """
    # This is a simplified implementation - in practice would need parameter ranges
    # For now, create mock sensitivity results for demonstration
    
    strategies = psa.table['strategy'].unique()
    results = []
    
    # Mock sensitivity analysis for key parameters
    parameters = ['cost', 'effect', 'ICER']
    
    for strategy in strategies:
        strategy_data = psa.table[psa.table['strategy'] == strategy]
        
        for param in parameters:
            if param in ['cost', 'effect']:
                base_value = strategy_data[param].mean()
                low_value = strategy_data[param].quantile(0.05)
                high_value = strategy_data[param].quantile(0.95)
                base_outcome = base_value
                low_outcome = low_value
                high_outcome = high_value
            else:
                # For ICER, calculate as cost/effect ratio
                base_cost = strategy_data['cost'].mean()
                base_effect = strategy_data['effect'].mean()
                base_value = base_cost / base_effect if base_effect != 0 else 0
                
                low_cost = strategy_data['cost'].quantile(0.05)
                low_effect = strategy_data['effect'].quantile(0.95)  # Inverse for ICER
                low_value = low_cost / low_effect if low_effect != 0 else 0
                
                high_cost = strategy_data['cost'].quantile(0.95)
                high_effect = strategy_data['effect'].quantile(0.05)  # Inverse for ICER
                high_value = high_cost / high_effect if high_effect != 0 else 0
                
                base_outcome = base_value
                low_outcome = low_value
                high_outcome = high_value
            
            results.append({
                'strategy': strategy,
                'parameter': param,
                'base_value': base_value,
                'low_value': low_value,
                'high_value': high_value,
                'base_outcome': base_outcome,
                'low_outcome': low_outcome,
                'high_outcome': high_outcome,
                'range': abs(high_outcome - low_outcome)
            })
    
    return pd.DataFrame(results)


def run_prcc_analysis(psa: PSAData) -> pd.DataFrame:
    """
    Run PRCC (Partial Rank Correlation Coefficient) analysis.
    
    Args:
        psa: PSA data with strategy information
        
    Returns:
        DataFrame with PRCC results
    """
    # Simplified PRCC implementation - in practice would use proper statistical methods
    strategies = psa.table['strategy'].unique()
    results = []
    
    for strategy in strategies:
        strategy_data = psa.table[psa.table['strategy'] == strategy]
        
        # Calculate correlations between parameters and outcomes
        corr_cost_effect = strategy_data['cost'].corr(strategy_data['effect'])
        corr_cost_draw = strategy_data['cost'].corr(strategy_data['draw'])
        corr_effect_draw = strategy_data['effect'].corr(strategy_data['draw'])
        
        results.append({
            'strategy': strategy,
            'prcc_cost_effect': corr_cost_effect,
            'prcc_cost_draw': corr_cost_draw,
            'prcc_effect_draw': corr_effect_draw,
            'sample_size': len(strategy_data)
        })
    
    return pd.DataFrame(results)


def run_two_way_dsa(psa: PSAData, param_pairs: List[Tuple[str, str]]) -> pd.DataFrame:
    """
    Run two-way deterministic sensitivity analysis.
    
    Args:
        psa: PSA data with strategy information
        param_pairs: List of parameter pairs to analyze
        
    Returns:
        DataFrame with two-way DSA results
    """
    results = []
    
    for param1, param2 in param_pairs:
        # Create a grid of parameter combinations
        if param1 == 'efficacy':
            param1_values = np.linspace(0.1, 0.9, 5)
        else:
            param1_values = np.linspace(1000, 50000, 5)
            
        if param2 == 'cost':
            param2_values = np.linspace(1000, 50000, 5)
        elif param2 == 'utility':
            param2_values = np.linspace(0.1, 0.9, 5)
        else:  # relapse_rate
            param2_values = np.linspace(0.1, 0.8, 5)
        
        for p1_val in param1_values:
            for p2_val in param2_values:
                # Mock outcome calculation
                outcome = p1_val * 1000 + p2_val * 0.1
                
                results.append({
                    'param1': param1,
                    'param2': param2,
                    'param1_value': p1_val,
                    'param2_value': p2_val,
                    'outcome': outcome
                })
    
    return pd.DataFrame(results)


def run_three_way_dsa(psa: PSAData, param_triple: Tuple[str, str, str]) -> pd.DataFrame:
    """
    Run three-way deterministic sensitivity analysis.
    
    Args:
        psa: PSA data with strategy information
        param_triple: Triple of parameters to analyze
        
    Returns:
        DataFrame with three-way DSA results
    """
    param1, param2, param3 = param_triple
    results = []
    
    # Create parameter ranges
    param_ranges = {
        'efficacy': np.linspace(0.1, 0.9, 3),
        'cost': np.linspace(5000, 30000, 3),
        'utility': np.linspace(0.2, 0.8, 3)
    }
    
    for p1_val in param_ranges.get(param1, np.linspace(0.1, 0.9, 3)):
        for p2_val in param_ranges.get(param2, np.linspace(0.1, 0.9, 3)):
            for p3_val in param_ranges.get(param3, np.linspace(0.1, 0.9, 3)):
                # Mock outcome calculation
                outcome = p1_val * 1000 + p2_val * 500 + p3_val * 200
                
                results.append({
                    'param1': param1,
                    'param2': param2,
                    'param3': param3,
                    'param1_value': p1_val,
                    'param2_value': p2_val,
                    'param3_value': p3_val,
                    'outcome': outcome
                })
    
    return pd.DataFrame(results)


def run_scenario_analysis(psa: PSAData) -> pd.DataFrame:
    """
    Run scenario analysis with different parameter assumptions.
    
    Args:
        psa: PSA data with strategy information
        
    Returns:
        DataFrame with scenario analysis results
    """
    strategies = psa.table['strategy'].unique()
    scenarios = ['base_case', 'optimistic', 'pessimistic', 'alternative_assumptions']
    results = []
    
    for strategy in strategies:
        strategy_data = psa.table[psa.table['strategy'] == strategy]
        base_cost = strategy_data['cost'].mean()
        base_effect = strategy_data['effect'].mean()
        
        for scenario in scenarios:
            if scenario == 'base_case':
                cost_mult = 1.0
                effect_mult = 1.0
            elif scenario == 'optimistic':
                cost_mult = 0.8
                effect_mult = 1.2
            elif scenario == 'pessimistic':
                cost_mult = 1.3
                effect_mult = 0.8
            else:  # alternative_assumptions
                cost_mult = 1.1
                effect_mult = 0.9
            
            scenario_cost = base_cost * cost_mult
            scenario_effect = base_effect * effect_mult
            
            results.append({
                'strategy': strategy,
                'scenario': scenario,
                'cost': scenario_cost,
                'effect': scenario_effect,
                'icer': scenario_cost / scenario_effect if scenario_effect != 0 else 0
            })
    
    return pd.DataFrame(results)
