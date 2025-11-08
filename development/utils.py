"""
Utility functions for TRD CEA analysis tools.

This module contains common utility functions used across different
analysis components.
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, Any, Union


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration parameters
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def save_results(results: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Save analysis results to a file.
    
    Args:
        results: Dictionary containing analysis results
        output_path: Path where results should be saved
    """
    with open(output_path, 'w') as file:
        yaml.dump(results, file, default_flow_style=False)


def calculate_icer(cost_new: float, cost_old: float, 
                  effect_new: float, effect_old: float) -> float:
    """
    Calculate incremental cost-effectiveness ratio (ICER).
    
    Args:
        cost_new: Cost of new intervention
        cost_old: Cost of old intervention
        effect_new: Effectiveness of new intervention
        effect_old: Effectiveness of old intervention
        
    Returns:
        ICER value (cost per unit of effectiveness)
    """
    if effect_new - effect_old == 0:
        return float('inf') if cost_new > cost_old else float('-inf')
    
    icer = (cost_new - cost_old) / (effect_new - effect_old)
    return icer


def calculate_nmb(cost: float, effect: float, wtp: float) -> float:
    """
    Calculate net monetary benefit.
    
    Args:
        cost: Cost of intervention
        effect: Effectiveness of intervention
        wtp: Willingness to pay threshold
        
    Returns:
        Net monetary benefit
    """
    nmb = effect * wtp - cost
    return nmb


def format_currency(amount: float, currency: str = 'AUD') -> str:
    """
    Format a monetary amount with currency symbol.
    
    Args:
        amount: Monetary amount
        currency: Currency code (default: 'AUD')
        
    Returns:
        Formatted currency string
    """
    return f"{currency} {amount:,.2f}"


def create_ce_plane_data(costs: list, effects: list) -> pd.DataFrame:
    """
    Create data for cost-effectiveness plane visualization.
    
    Args:
        costs: List of costs for different interventions
        effects: List of effects for different interventions
        
    Returns:
        DataFrame with cost and effect data
    """
    df = pd.DataFrame({
        'cost': costs,
        'effect': effects,
        'strategy': [f'Strategy {i+1}' for i in range(len(costs))]
    })
    return df


def calculate_discount_factor(rate: float, period: int) -> float:
    """
    Calculate discount factor for a given rate and time period.
    
    Args:
        rate: Discount rate (as decimal, e.g., 0.035 for 3.5%)
        period: Time period
        
    Returns:
        Discount factor
    """
    return 1 / (1 + rate) ** period


def calculate_paf(rate: float, periods: int) -> float:
    """
    Calculate present value of an annuity factor (P/A, i%, n).
    
    Args:
        rate: Interest/discount rate (as decimal)
        periods: Number of periods
        
    Returns:
        Present value of annuity factor
    """
    if rate == 0:
        return periods
    return (1 - (1 + rate) ** -periods) / rate