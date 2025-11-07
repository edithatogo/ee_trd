"""
Configuration validation module for TRD CEA toolkit.

This module provides functions for validating configuration parameters and values.
"""

from typing import Dict, Any, Tuple, List
import pandas as pd


def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate configuration parameters.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for required top-level keys
    required_keys = ['analysis', 'strategies']
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required configuration key: {key}")
    
    # Validate analysis section
    if 'analysis' in config:
        analysis = config['analysis']
        required_analysis_keys = ['time_horizon', 'wtp_threshold']
        for key in required_analysis_keys:
            if key not in analysis:
                errors.append(f"Missing required analysis parameter: {key}")
        
        # Validate time horizon
        time_horizon = analysis.get('time_horizon', 0)
        if not isinstance(time_horizon, (int, float)) or time_horizon <= 0:
            errors.append(f"'time_horizon' must be a positive number, got: {time_horizon}")
        
        # Validate WTP threshold
        wtp_threshold = analysis.get('wtp_threshold', 0)
        if not isinstance(wtp_threshold, (int, float)) or wtp_threshold <= 0:
            errors.append(f"'wtp_threshold' must be a positive number, got: {wtp_threshold}")
    
    # Validate strategies section
    if 'strategies' in config:
        strategies = config['strategies']
        if not isinstance(strategies, dict) or len(strategies) < 2:
            errors.append("Strategies must be a dictionary with at least 2 strategies")
        else:
            for strategy_name, strategy_params in strategies.items():
                if not isinstance(strategy_params, dict):
                    errors.append(f"Strategy '{strategy_name}' parameters must be a dictionary")
                    continue
                
                # Check for required strategy parameters
                if 'cost' not in strategy_params:
                    errors.append(f"Strategy '{strategy_name}' missing required 'cost' parameter")
                else:
                    cost = strategy_params['cost']
                    if not isinstance(cost, (int, float)) or cost < 0:
                        errors.append(f"Strategy '{strategy_name}' cost must be a non-negative number, got: {cost}")
                
                if 'effect' not in strategy_params:
                    errors.append(f"Strategy '{strategy_name}' missing required 'effect' parameter")
                else:
                    effect = strategy_params['effect']
                    if not isinstance(effect, (int, float)) or effect < 0:
                        errors.append(f"Strategy '{strategy_name}' effect must be a non-negative number, got: {effect}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_analysis_parameters(
    strategies: List[str],
    costs: List[float], 
    effects: List[float],
    wtp_threshold: float
) -> Tuple[bool, List[str]]:
    """
    Validate basic analysis parameters.
    
    Args:
        strategies: List of strategy names
        costs: List of costs (same length as strategies)
        effects: List of effects (same length as strategies)
        wtp_threshold: Willingness-to-pay threshold
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check equal lengths
    if len(costs) != len(effects) or len(costs) != len(strategies):
        errors.append(f"Mismatched lengths: strategies={len(strategies)}, costs={len(costs)}, effects={len(effects)}")
    
    # Check for valid numeric values
    for i, (cost, effect) in enumerate(zip(costs, effects)):
        if not isinstance(cost, (int, float)):
            errors.append(f"Cost at index {i} is not numeric: {cost}")
        elif cost < 0:
            errors.append(f"Cost at index {i} is negative: {cost}")
        
        if not isinstance(effect, (int, float)):
            errors.append(f"Effect at index {i} is not numeric: {effect}")
        elif effect < 0:
            errors.append(f"Effect at index {i} is negative: {effect}")
    
    # Validate WTP
    if not isinstance(wtp_threshold, (int, float)) or wtp_threshold <= 0:
        errors.append(f"WTP threshold must be positive, got: {wtp_threshold}")
    
    # Check for at least one strategy
    if len(strategies) < 1:
        errors.append("At least one strategy is required")
    
    return len(errors) == 0, errors


def validate_psa_parameters(
    psa_data: pd.DataFrame,
    required_columns: List[str] = ['strategy', 'cost', 'effect', 'draw']
) -> Tuple[bool, List[str]]:
    """
    Validate PSA parameter structure.
    
    Args:
        psa_data: DataFrame with PSA draws
        required_columns: Required columns in the PSA data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for required columns
    for col in required_columns:
        if col not in psa_data.columns:
            errors.append(f"Missing required column in PSA data: {col}")
    
    # Validate data types
    if 'cost' in psa_data.columns:
        if not all(pd.api.types.is_numeric_dtype(psa_data['cost'])):
            errors.append("Cost column must contain numeric values")
        elif (psa_data['cost'] < 0).any():
            errors.append("Cost values must be non-negative")
    
    if 'effect' in psa_data.columns:
        if not all(pd.api.types.is_numeric_dtype(psa_data['effect'])):
            errors.append("Effect column must contain numeric values")
        elif (psa_data['effect'] < 0).any():
            errors.append("Effect values must be non-negative")
    
    # Validate draw uniqueness
    if 'draw' in psa_data.columns:
        if psa_data['draw'].duplicated().any():
            errors.append("Draw IDs must be unique")
    
    return len(errors) == 0, errors


def validate_bia_parameters(
    bia_parameters: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate Budget Impact Analysis parameters.
    
    Args:
        bia_parameters: Dictionary of BIA parameters
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    required_keys = [
        'time_horizon', 'target_population', 'market_share_scenarios',
        'pricing', 'perspective'
    ]
    
    for key in required_keys:
        if key not in bia_parameters:
            errors.append(f"Missing required BIA parameter: {key}")
    
    # Validate time horizon
    if 'time_horizon' in bia_parameters:
        th = bia_parameters['time_horizon']
        if not isinstance(th, (int, float)) or th <= 0:
            errors.append(f"BIA time_horizon must be positive, got: {th}")
    
    # Validate target population
    if 'target_population' in bia_parameters:
        tp = bia_parameters['target_population']
        if not isinstance(tp, (int, float)) or tp <= 0:
            errors.append(f"BIA target_population must be positive, got: {tp}")
    
    # Validate market share scenarios
    if 'market_share_scenarios' in bia_parameters:
        mss = bia_parameters['market_share_scenarios']
        if not isinstance(mss, list) or len(mss) == 0:
            errors.append("Market share scenarios must be a non-empty list")
    
    # Validate pricing
    if 'pricing' in bia_parameters:
        pricing = bia_parameters['pricing']
        if not isinstance(pricing, dict):
            errors.append("Pricing must be a dictionary")
    
    return len(errors) == 0, errors


def validate_voi_parameters(
    voi_parameters: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate Value of Information analysis parameters.
    
    Args:
        voi_parameters: Dictionary of VOI parameters
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    required_keys = [
        'n_simulations', 'strategies', 'wtp_threshold',
        'uncertainty_parameters'
    ]
    
    for key in required_keys:
        if key not in voi_parameters:
            errors.append(f"Missing required VOI parameter: {key}")
    
    # Validate simulation count
    if 'n_simulations' in voi_parameters:
        ns = voi_parameters['n_simulations']
        if not isinstance(ns, int) or ns <= 0:
            errors.append(f"VOI n_simulations must be a positive integer, got: {ns}")
    
    # Validate strategies
    if 'strategies' in voi_parameters:
        strategies = voi_parameters['strategies']
        if not isinstance(strategies, list) or len(strategies) < 2:
            errors.append("VOI strategies must be a list with at least 2 strategies")
    
    # Validate WTP
    if 'wtp_threshold' in voi_parameters:
        wtp = voi_parameters['wtp_threshold']
        if not isinstance(wtp, (int, float)) or wtp <= 0:
            errors.append(f"VOI wtp_threshold must be positive, got: {wtp}")
    
    # Validate uncertainty parameters
    if 'uncertainty_parameters' in voi_parameters:
        up = voi_parameters['uncertainty_parameters']
        if not isinstance(up, dict):
            errors.append("Uncertainty parameters must be a dictionary")
    
    return len(errors) == 0, errors


def validate_dcea_parameters(
    dcea_parameters: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate Distributional CEA parameters.
    
    Args:
        dcea_parameters: Dictionary of DCEA parameters
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    required_keys = [
        'equity_weights', 'population_strata', 'strategies',
        'wtp_threshold', 'time_horizon'
    ]
    
    for key in required_keys:
        if key not in dcea_parameters:
            errors.append(f"Missing required DCEA parameter: {key}")
    
    # Validate equity weights
    if 'equity_weights' in dcea_parameters:
        eq_weights = dcea_parameters['equity_weights']
        if not isinstance(eq_weights, dict):
            errors.append("DCEA equity_weights must be a dictionary")
    
    # Validate population strata
    if 'population_strata' in dcea_parameters:
        pop_strata = dcea_parameters['population_strata']
        if not isinstance(pop_strata, list) or len(pop_strata) == 0:
            errors.append("DCEA population_strata must be a non-empty list")
    
    return len(errors) == 0, errors