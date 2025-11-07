"""
Net Monetary Benefit (NMB) calculation module for health economic evaluation.
"""

import pandas as pd
import numpy as np
from typing import Union, Dict, List


def compute_nmb(cost: float, effect: float, wtp_threshold: float) -> float:
    """
    Compute net monetary benefit for a single strategy.
    
    Args:
        cost: Cost of the strategy
        effect: Health effect (QALYs) of the strategy
        wtp_threshold: Willingness-to-pay threshold per QALY
        
    Returns:
        Net monetary benefit
    """
    return effect * wtp_threshold - cost


def calculate_expected_value_of_perfect_information(
    strategy_results: List[Dict], 
    wtp_threshold: float,
    n_simulations: int = 1000
) -> float:
    """
    Calculate Expected Value of Perfect Information (EVPI).
    
    EVPI = E[max_i(NMB_i(θ))] - max_i(E[NMB_i(θ)])
    
    Args:
        strategy_results: List of dictionaries containing 'cost' and 'effect' arrays
        wtp_threshold: Willingness-to-pay threshold per QALY
        n_simulations: Number of simulations to average over
        
    Returns:
        EVPI in monetary units
    """
    # Calculate NMB for each strategy across simulations
    nmb_matrices = []
    
    for strategy in strategy_results:
        costs = np.array(strategy['cost'])[:n_simulations]  # Take first n_simulations
        effects = np.array(strategy['effect'])[:n_simulations]
        
        nmb_array = compute_nmb(costs, effects, wtp_threshold)
        nmb_matrices.append(nmb_array)
    
    # Convert to array (strategies x simulations)
    nmb_array = np.array(nmb_matrices)
    
    # Calculate EVPI
    # E[max_i(NMB_i(θ))]: Expected value of choosing best strategy for each simulation
    max_nmb_per_simulation = np.max(nmb_array, axis=0)  # Max NMB for each simulation
    expected_max_nmb = np.mean(max_nmb_per_simulation)
    
    # max_i(E[NMB_i(θ))]: Best strategy based on expected values
    expected_nmb_per_strategy = np.mean(nmb_array, axis=1)  # Expected NMB for each strategy
    max_expected_nmb = np.max(expected_nmb_per_strategy)
    
    evpi = expected_max_nmb - max_expected_nmb
    return max(0.0, evpi)  # EVPI is non-negative


def argmax_with_tiebreak(array: np.ndarray, random_state: int = None) -> int:
    """
    Find the index of the maximum value in an array, with random tie-breaking.
    
    Args:
        array: Array to find argmax for
        random_state: Random seed for tie-breaking
        
    Returns:
        Index of maximum value (with random tie-break if multiple maximums)
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    max_val = np.max(array)
    max_indices = np.where(array == max_val)[0]
    
    if len(max_indices) == 1:
        return max_indices[0]
    else:
        # Randomly select one of the tied indices
        return np.random.choice(max_indices)


def compute_nmb_array(
    costs: Union[np.ndarray, List[float]], 
    effects: Union[np.ndarray, List[float]], 
    wtp_threshold: float
) -> np.ndarray:
    """
    Compute net monetary benefit for arrays of costs and effects.
    
    Args:
        costs: Array of costs
        effects: Array of effects (QALYs)
        wtp_threshold: Willingness-to-pay threshold per QALY
        
    Returns:
        Array of net monetary benefits
    """
    costs = np.asarray(costs)
    effects = np.asarray(effects)
    
    return compute_nmb(costs, effects, wtp_threshold)


def calculate_ce_plane_coordinates(
    costs: List[float], 
    effects: List[float], 
    reference_idx: int = 0
) -> (List[float], List[float]):
    """
    Calculate coordinates for cost-effectiveness plane.
    
    Args:
        costs: List of intervention costs
        effects: List of intervention effects
        reference_idx: Index of reference intervention
        
    Returns:
        Tuple of (incremental_costs, incremental_effects)
    """
    ref_cost = costs[reference_idx]
    ref_effect = effects[reference_idx]
    
    inc_costs = [cost - ref_cost for cost in costs]
    inc_effects = [effect - ref_effect for effect in effects]
    
    return inc_costs, inc_effects


def calculate_icer(
    cost_new: float,
    cost_old: float,
    effect_new: float,
    effect_old: float,
    wtp_threshold: float = 50000
) -> Union[float, str]:
    """
    Calculate Incremental Cost-Effectiveness Ratio.
    
    Args:
        cost_new: Cost of new intervention
        cost_old: Cost of old intervention
        effect_new: Effect of new intervention
        effect_old: Effect of old intervention
        wtp_threshold: Willingness-to-pay threshold per QALY
        
    Returns:
        ICER value or description if dominated
    """
    inc_cost = cost_new - cost_old
    inc_effect = effect_new - effect_old
    
    if inc_effect == 0:
        if inc_cost > 0:
            return float('inf')  # Dominated
        elif inc_cost < 0:
            return float('-inf')  # Dominates
        else:
            return 0.0  # No difference
    
    icer = inc_cost / inc_effect
    
    # Check for dominance
    if inc_cost < 0 and inc_effect > 0:
        return "Dominates reference"  # New intervention is both cheaper and more effective
    elif inc_cost > 0 and inc_effect < 0:
        return "Dominated by reference"  # New intervention is both more costly and less effective
    
    return icer


def calculate_inmb(
    cost_new: float,
    cost_old: float,
    effect_new: float,
    effect_old: float,
    wtp_threshold: float
) -> float:
    """
    Calculate Incremental Net Monetary Benefit.
    
    Args:
        cost_new: Cost of new intervention
        cost_old: Cost of old intervention
        effect_new: Effect of new intervention
        effect_old: Effect of old intervention
        wtp_threshold: Willingness-to-pay threshold per QALY
        
    Returns:
        Incremental Net Monetary Benefit
    """
    inc_cost = cost_new - cost_old
    inc_effect = effect_new - effect_old
    
    return inc_effect * wtp_threshold - inc_cost


def calculate_probability_ce(
    nmb_values: Union[np.ndarray, List[float]], 
    threshold: float = 0
) -> float:
    """
    Calculate probability that net monetary benefit exceeds threshold.
    
    Args:
        nmb_values: Array/list of NMB values
        threshold: Threshold for clinical significance (default 0)
        
    Returns:
        Probability that NMB > threshold
    """
    nmb_array = np.asarray(nmb_values)
    return np.mean(nmb_array > threshold)


def calculate_eib(
    costs: List[float], 
    effects: List[float], 
    wtp_threshold: float,
    strategy_idx: int,
    reference_idx: int = 0
) -> float:
    """
    Calculate Expected Incremental Benefit.
    
    Args:
        costs: List of intervention costs
        effects: List of intervention effects
        wtp_threshold: Willingness-to-pay threshold per QALY
        strategy_idx: Index of the strategy to compare
        reference_idx: Index of reference strategy (default 0)
        
    Returns:
        Expected Incremental Benefit
    """
    inc_effect = effects[strategy_idx] - effects[reference_idx]
    inc_cost = costs[strategy_idx] - costs[reference_idx]
    
    return inc_effect * wtp_threshold - inc_cost


def create_ce_plane_data(
    strategies: List[str],
    costs: List[float],
    effects: List[float],
    reference_strategy: str = None
) -> pd.DataFrame:
    """
    Create cost-effectiveness plane data with proper reference comparison.
    
    Args:
        strategies: List of strategy names
        costs: List of strategy costs
        effects: List of strategy effects
        reference_strategy: Name of reference strategy (defaults to first)
        
    Returns:
        DataFrame with strategy, cost, effect, and incremental values
    """
    if reference_strategy is None:
        ref_idx = 0
    else:
        ref_idx = strategies.index(reference_strategy)
    
    ref_cost = costs[ref_idx]
    ref_effect = effects[ref_idx]
    
    # Create DataFrame
    df = pd.DataFrame({
        'strategy': strategies,
        'cost': costs,
        'effect': effects
    })
    
    # Calculate incremental values relative to reference
    df['incremental_cost'] = df['cost'] - ref_cost
    df['incremental_effect'] = df['effect'] - ref_effect
    
    # Calculate ICERs where appropriate (relative to reference)
    df['icer'] = np.nan
    for i in range(len(df)):
        if i != ref_idx:
            inc_cost = df.iloc[i]['incremental_cost']
            inc_effect = df.iloc[i]['incremental_effect']
            
            if inc_effect != 0:
                df.iloc[i, df.columns.get_loc('icer')] = inc_cost / inc_effect
    
    # Calculate NMB relative to reference
    df['nmb_vs_reference'] = df['incremental_effect'] * 50000 - df['incremental_cost']  # Using default WTP
    
    return df


def calculate_cost_effectiveness_acceptability_curve(
    psa_results: pd.DataFrame,
    strategies: List[str],
    wtp_thresholds: Union[np.ndarray, List[float]] = None
) -> pd.DataFrame:
    """
    Calculate Cost-Effectiveness Acceptability Curve (CEAC).
    
    Args:
        psa_results: DataFrame with columns: 'draw', 'strategy', 'cost', 'effect'
        strategies: List of strategy names in the analysis
        wtp_thresholds: Array of willingness-to-pay thresholds
        
    Returns:
        DataFrame with WTP threshold and probability of cost-effectiveness for each strategy
    """
    if wtp_thresholds is None:
        wtp_thresholds = np.linspace(0, 100000, 21)
    
    results = []
    
    for wtp in wtp_thresholds:
        # Calculate NMB for each strategy at this WTP level
        psa_results['nmb'] = psa_results['effect'] * wtp - psa_results['cost']
        
        # For each simulation draw, find the optimal strategy
        optimal_by_draw = psa_results.loc[psa_results.groupby('draw')['nmb'].idxmax()]
        
        # Calculate probability each strategy is optimal
        probs = optimal_by_draw['strategy'].value_counts(normalize=True)
        
        # Add to results
        result_row = {'wtp_threshold': wtp}
        for strategy in strategies:
            result_row[f'prob_ce_{strategy}'] = probs.get(strategy, 0.0)
        results.append(result_row)
    
    return pd.DataFrame(results)