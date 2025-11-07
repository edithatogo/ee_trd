"""
Utility functions for health economic evaluation.

These functions provide basic calculations for cost-effectiveness analysis.
"""

def calculate_icer(cost_new, cost_ref, effect_new, effect_ref):
    """
    Calculate Incremental Cost-Effectiveness Ratio.
    
    Args:
        cost_new: Cost of the new intervention
        cost_ref: Cost of the reference intervention
        effect_new: Effectiveness of the new intervention
        effect_ref: Effectiveness of the reference intervention
    
    Returns:
        ICER value (cost per unit effect)
    """
    inc_cost = cost_new - cost_ref
    inc_effect = effect_new - effect_ref
    
    if inc_effect == 0:
        return float('inf') if inc_cost > 0 else float('-inf') if inc_cost < 0 else 0.0
    
    return inc_cost / inc_effect


def calculate_nmb(cost, effect, wtp_threshold):
    """
    Calculate Net Monetary Benefit.
    
    Args:
        cost: Total cost of intervention
        effect: Total effectiveness (QALYs) of intervention
        wtp_threshold: Willingness-to-pay threshold per unit of effect
    
    Returns:
        Net Monetary Benefit
    """
    return effect * wtp_threshold - cost


def calculate_icr(cost, effect):
    """
    Calculate Cost-Effectiveness Ratio.
    
    Args:
        cost: Total cost of intervention
        effect: Total effectiveness of intervention
        
    Returns:
        Cost per unit of effect
    """
    if effect == 0:
        return float('inf') if cost > 0 else 0.0
    
    return cost / effect


def calculate_dalys_averted(mortality_rate, morbidities, time_horizon, discount_rate=0.035):
    """
    Calculate DALYs averted with discounting.
    
    Args:
        mortality_rate: Reduction in mortality rate
        morbidities: Morbidity reduction measures
        time_horizon: Analysis time horizon in years
        discount_rate: Discount rate
        
    Returns:
        DALYs averted over time horizon
    """
    # Simplified calculation for demonstration
    daly_reduction_per_year = mortality_rate + sum(morbidity * 0.5 for morbidity in morbidities)
    
    # Apply discounting
    discounted_dalys = 0
    for year in range(1, int(time_horizon) + 1):
        discount_factor = 1 / (1 + discount_rate) ** year
        discounted_dalys += daly_reduction_per_year * discount_factor
    
    return discounted_dalys