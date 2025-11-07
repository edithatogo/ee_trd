"""
Analysis execution module for TRD CEA Toolkit

This module provides functions for executing different types of health economic analyses.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def run_analysis_pipeline(
    config_path: str,
    analysis_type: str = "cea",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a complete analysis pipeline based on configuration.

    Args:
        config_path: Path to configuration file
        analysis_type: Type of analysis to run ('cea', 'dcea', 'voi', 'bia')
        output_dir: Optional output directory

    Returns:
        Dictionary containing analysis results
    """
    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate configuration
    _validate_config(config, analysis_type)

    # Execute appropriate analysis based on type
    if analysis_type == "cea":
        from trd_cea.models.cea_engine import run_cea
        results = run_cea(config)
    elif analysis_type == "dcea":
        from trd_cea.models.dcea import run_dcea
        results = run_dcea(config)
    elif analysis_type == "voi":
        from trd_cea.models.value_of_info import run_voi
        results = run_voi(config)
    elif analysis_type == "bia":
        from trd_cea.models.bia_engine import run_bia
        results = run_bia(config)
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")

    # Save results if output directory specified
    if output_dir:
        _save_results(results, output_dir, analysis_type)

    return results


def _validate_config(config: Dict[str, Any], analysis_type: str) -> bool:
    """Validate configuration for the specified analysis type."""
    required_keys = ['strategies', 'time_horizon', 'wtp_threshold']
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
    
    # Validate strategies
    if 'strategies' not in config or not isinstance(config['strategies'], dict):
        raise ValueError("Configuration must contain 'strategies' dictionary")
    
    # Validate time horizon
    if not isinstance(config['time_horizon'], (int, float)) or config['time_horizon'] <= 0:
        raise ValueError("'time_horizon' must be a positive number")
    
    # Validate WTP threshold
    if not isinstance(config['wtp_threshold'], (int, float)) or config['wtp_threshold'] <= 0:
        raise ValueError("'wtp_threshold' must be a positive number")
    
    return True


def _save_results(results: Dict[str, Any], output_dir: str, analysis_type: str):
    """Save analysis results to output directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save main results as CSV
    if 'results_df' in results:
        results['results_df'].to_csv(output_path / f"{analysis_type}_results.csv", index=False)
    
    # Save parameters used
    params_file = output_path / f"{analysis_type}_parameters_used.yaml"
    with open(params_file, 'w') as f:
        import yaml
        yaml.dump(results.get('parameters_used', {}), f)
    
    # Save summary metrics
    summary_file = output_path / f"{analysis_type}_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Analysis type: {analysis_type}\n")
        f.write(f"Number of strategies: {results.get('n_strategies', 'N/A')}\n")
        f.write(f"Time horizon: {results.get('time_horizon', 'N/A')} years\n")
        f.write(f"WTP threshold: ${results.get('wtp_threshold', 'N/A'):,}/QALY\n")
        f.write(f"Reference strategy: {results.get('reference_strategy', 'N/A')}\n")
        
        if 'icers' in results:
            f.write("\nICERs:\n")
            for strategy, icer in results.get('icers', {}).items():
                f.write(f"  {strategy}: ${icer:,.2f}/QALY\n")


def run_probabilistic_sensitivity_analysis(
    config: Dict[str, Any],
    n_simulations: int = 1000
) -> Dict[str, Any]:
    """
    Run probabilistic sensitivity analysis using Monte Carlo simulation.

    Args:
        config: Configuration dictionary
        n_simulations: Number of Monte Carlo simulations

    Returns:
        PSA results dictionary
    """
    # This would implement a full PSA using the configuration
    # For now, we'll return a mock result structure
    strategies = list(config.get('strategies', {}).keys())
    
    # Generate mock PSA results based on config
    psa_results = {
        'strategy': [],
        'cost_mean': [],
        'cost_std': [],
        'effect_mean': [],
        'effect_std': [],
        'nmb_mean': [],
        'nmb_std': [],
        'probability_ce': []  # Probability of being cost-effective
    }
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    for i, strategy in enumerate(strategies):
        # Generate mock results (in a real implementation would run actual Monte Carlo)
        psa_results['strategy'].append(strategy)
        psa_results['cost_mean'].append(5000 + i*1000 + np.random.normal(0, 500))
        psa_results['cost_std'].append(500 + np.abs(np.random.normal(0, 100)))  # Ensure positive std
        psa_results['effect_mean'].append(0.6 + i*0.1 + np.random.normal(0, 0.05))
        psa_results['effect_std'].append(0.05 + np.abs(np.random.normal(0, 0.01)))  # Ensure positive std
        
        # Calculate mean NMB
        wtp = config.get('wtp_threshold', 50000)
        mean_nmb = psa_results['effect_mean'][-1] * wtp - psa_results['cost_mean'][-1]
        psa_results['nmb_mean'].append(mean_nmb)
        psa_results['nmb_std'].append(2000)  # Mock NMB standard deviation
        
        # Mock probability of cost-effectiveness (in reality this would be calculated from PSA draws)
        psa_results['probability_ce'].append(min(1.0, max(0.0, 0.7 + i*0.1 + np.random.normal(0, 0.1))))  # Increasing probability with better strategies
    
    return {
        'psa_results': pd.DataFrame(psa_results),
        'n_simulations': n_simulations,
        'parameters_used': config,
        'analysis_type': 'psa'
    }


def run_deterministic_sensitivity_analysis(
    config: Dict[str, Any],
    parameter_name: str,
    parameter_range: list
) -> Dict[str, Any]:
    """
    Run deterministic one-way sensitivity analysis.

    Args:
        config: Base configuration dictionary
        parameter_name: Name of parameter to vary
        parameter_range: Range of values to test for the parameter

    Returns:
        DSA results dictionary
    """
    base_results = run_analysis_pipeline(config, analysis_type="cea", output_dir=None)
    
    dsa_results = []
    
    for value in parameter_range:
        # Temporarily modify the parameter
        temp_config = _modify_config_parameter(config.copy(), parameter_name, value)
        
        # Run analysis with modified parameter
        result = run_analysis_pipeline(temp_config, analysis_type="cea", output_dir=None)
        
        dsa_results.append({
            'parameter': parameter_name,
            'parameter_value': value,
            'icers': result.get('icers', {}),
            'nmbs': result.get('nmbs', {})
        })
    
    return {
        'dsa_results': dsa_results,
        'parameter_name': parameter_name,
        'parameter_range': parameter_range,
        'base_results': base_results
    }


def _modify_config_parameter(config: Dict, param_path: str, new_value: Any) -> Dict:
    """
    Modify a parameter in the configuration at the specified path.

    Args:
        config: Configuration dictionary
        param_path: Dot-separated path to the parameter
        new_value: New value for the parameter

    Returns:
        Modified configuration dictionary
    """
    import copy
    modified_config = copy.deepcopy(config)
    
    # Split path and navigate to the parameter
    path_parts = param_path.split('.')
    current = modified_config
    
    for part in path_parts[:-1]:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise ValueError(f"Configuration path '{param_path}' not found")
    
    final_part = path_parts[-1]
    if isinstance(current, dict) and final_part in current:
        current[final_part] = new_value
    else:
        raise ValueError(f"Parameter '{final_part}' not found in configuration")
    
    return modified_config


def run_headroom_analysis(
    config: Dict[str, Any],
    strategy_to_analyze: str
) -> Dict[str, float]:
    """
    Run headroom analysis to determine maximum acceptable price.

    Args:
        config: Configuration dictionary
        strategy_to_analyze: Strategy to analyze for headroom

    Returns:
        Headroom analysis results
    """
    # Reference strategy is typically the standard of care
    strategies = list(config['strategies'].keys())
    reference_strategy = strategies[0] if strategy_to_analyze != strategies[0] else strategies[1]
    
    # Get base results
    base_results = run_analysis_pipeline(config, analysis_type="cea", output_dir=None)
    
    # Calculate maximum acceptable cost for the strategy to remain cost-effective
    wtp_threshold = config['wtp_threshold']
    
    ref_cost = config['strategies'][reference_strategy].get('cost', 5000)
    ref_effect = config['strategies'][reference_strategy].get('effect', 0.6)
    
    strategy_cost = config['strategies'][strategy_to_analyze].get('cost', 7000)
    strategy_effect = config['strategies'][strategy_to_analyze].get('effect', 0.8)
    
    # Calculate maximum cost to maintain ICER below WTP threshold
    if strategy_effect > ref_effect:
        max_acceptable_cost = ref_cost + wtp_threshold * (strategy_effect - ref_effect)
        headroom = max_acceptable_cost - strategy_cost
    else:
        # If strategy is less effective, headroom is negative
        # In this case, calculate max acceptable cost as the cost that would result in same NMB as reference
        ref_nmb = ref_effect * wtp_threshold - ref_cost
        max_acceptable_cost = strategy_effect * wtp_threshold - ref_nmb
        headroom = max_acceptable_cost - strategy_cost
    
    return {
        'strategy': strategy_to_analyze,
        'reference_strategy': reference_strategy,
        'current_cost': strategy_cost,
        'max_acceptable_cost': max_acceptable_cost,
        'headroom': headroom,
        'wtp_threshold': wtp_threshold,
        'analysis_type': 'headroom'
    }