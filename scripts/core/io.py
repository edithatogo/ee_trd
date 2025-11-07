"""
PSA Data Container for Health Economic Evaluation

This module defines the PSAData class and related structures for handling
probabilistic sensitivity analysis data in health economic evaluations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np


@dataclass
class PSAConfig:
    """Configuration for PSA analysis."""
    strategies: List[str]
    base_case: str
    wtp_threshold: float
    perspective: str
    jurisdiction: str
    n_iterations: int
    analysis_type: str
    parameters: Dict[str, Any]


@dataclass
class PSAData:
    """Container for PSA data and configuration."""
    
    table: pd.DataFrame  # Must have columns: draw, strategy, cost, effect
    config: PSAConfig
    draws: int
    
    @property
    def strategies(self) -> List[str]:
        """Get list of strategies."""
        return self.config.strategies
    
    @property
    def base(self) -> str:
        """Get base strategy."""
        return self.config.base_case


def create_sample_psa_data(
    strategies: List[str] = None,
    n_draws: int = 1000,
    seed: int = 42
) -> PSAData:
    """
    Create sample PSA data for testing and demos.
    
    Args:
        strategies: List of strategy names
        n_draws: Number of PSA draws
        seed: Random seed for reproducibility
    
    Returns:
        PSAData object with sample data
    """
    if strategies is None:
        strategies = ['ECT', 'IV-KA', 'PO-KA']
    
    np.random.seed(seed)
    
    # Create sample data
    data = []
    base_cost = 5000
    base_effect = 0.6
    
    for strategy in strategies:
        if strategy == 'IV-KA':
            cost_multiplier, effect_multiplier = 1.2, 1.25
        elif strategy == 'PO-KA':
            cost_multiplier, effect_multiplier = 0.9, 1.15
        else:  # ECT
            cost_multiplier, effect_multiplier = 1.0, 1.0
        
        for draw in range(n_draws):
            # Add some random variation
            cost = base_cost * cost_multiplier * np.random.normal(1.0, 0.1)
            effect = max(0.1, base_effect * effect_multiplier * np.random.normal(1.0, 0.1))
            
            data.append({
                'draw': draw,
                'strategy': strategy,
                'cost': max(100, cost),  # Ensure positive costs
                'effect': max(0.01, effect)  # Ensure positive effects
            })
    
    df = pd.DataFrame(data)
    
    config = PSAConfig(
        strategies=strategies,
        base_case='ECT',
        wtp_threshold=50000,
        perspective='healthcare',
        jurisdiction='AU',
        n_iterations=n_draws,
        analysis_type='cea',
        parameters={}
    )
    
    return PSAData(table=df, config=config, draws=n_draws)