"""
V4 Budget Impact Analysis Engine

Implements BIA with market share modeling, population scaling, and implementation costs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict

import numpy as np
import pandas as pd

from analysis.core.io import PSAData


@dataclass
class BIAResult:
    """Container for Budget Impact Analysis results."""
    
    annual_budget_impact: pd.DataFrame      # Year-by-year budget impact
    cumulative_budget_impact: pd.DataFrame  # Cumulative impact
    market_share_evolution: pd.DataFrame    # Market share over time
    cost_breakdown: pd.DataFrame            # Cost components
    perspective: str
    jurisdiction: Optional[str]


def calculate_market_share_evolution(
    initial_shares: Dict[str, float],
    final_shares: Dict[str, float],
    time_horizon: int,
    adoption_curve: str = 'linear'
):
    """
    Calculate market share evolution over time.
    
    Args:
        initial_shares: Initial market shares by strategy
        final_shares: Final market shares by strategy
        time_horizon: Number of years
        adoption_curve: 'linear' or 's-curve'
    
    Returns:
        DataFrame with market shares over time
    """
    strategies = list(initial_shares.keys())
    years = list(range(time_horizon + 1))
    
    market_share_rows = []
    
    for year in years:
        if adoption_curve == 'linear':
            # Linear interpolation
            fraction = year / time_horizon if time_horizon > 0 else 1
        elif adoption_curve == 's-curve':
            # S-curve (logistic):
            midpoint = time_horizon / 2
            steepness = 0.5
            fraction = 1 / (1 + np.exp(-steepness * (year - midpoint)))
        else:
            fraction = year / time_horizon if time_horizon > 0 else 1
        
        for strategy in strategies:
            initial = initial_shares.get(strategy, 0)
            final = final_shares.get(strategy, 0)
            current_share = initial + (final - initial) * fraction
            
            market_share_rows.append({
                'year': year,
                'strategy': strategy,
                'market_share': current_share
            })
    
    return pd.DataFrame(market_share_rows)


def calculate_budget_impact(
    psa: PSAData,
    population_size: int,
    time_horizon: int,
    initial_market_shares: Dict[str, float],
    final_market_shares: Dict[str, float],
    implementation_costs: Optional[Dict[str, float]] = None,
    discount_rate: float = 0.05,
    adoption_curve: str = 'linear'
) -> BIAResult:
    """
    Calculate budget impact analysis.

    Args:
        psa: PSAData object
        population_size: Eligible population size
        time_horizon: Number of years
        initial_market_shares: Initial market shares (current scenario)
        final_market_shares: Final market shares (new scenario)
        implementation_costs: One-time implementation costs by strategy
        discount_rate: Annual discount rate
        adoption_curve: Market adoption pattern

    Returns:
        BIAResult with complete budget impact analysis
    """
    # Calculate market share evolution
    market_shares = calculate_market_share_evolution(
        initial_market_shares,
        final_market_shares,
        time_horizon,
        adoption_curve
    )
    
    # Get mean costs per patient
    mean_costs = psa.table.groupby('strategy')['cost'].mean().to_dict()
    
    # Calculate annual budget impact
    annual_rows = []
    
    for year in range(time_horizon + 1):
        year_shares = market_shares[market_shares['year'] == year]
        
        # Current scenario cost
        current_cost = 0
        for _, row in year_shares.iterrows():
            strategy = row['strategy']
            initial_share = initial_market_shares.get(strategy, 0)
            cost_per_patient = mean_costs.get(strategy, 0)
            current_cost += initial_share * cost_per_patient * population_size
        
        # New scenario cost
        new_cost = 0
        for _, row in year_shares.iterrows():
            strategy = row['strategy']
            share = row['market_share']
            cost_per_patient = mean_costs.get(strategy, 0)
            new_cost += share * cost_per_patient * population_size
        
        # Add implementation costs in year 0
        implementation_cost = 0
        if year == 0 and implementation_costs:
            for strategy, cost in implementation_costs.items():
                share_change = final_market_shares.get(strategy, 0) - initial_market_shares.get(strategy, 0)
                if share_change > 0:
                    implementation_cost += cost
        
        # Discount factor
        discount_factor = 1 / ((1 + discount_rate) ** year)
        
        # Budget impact
        budget_impact = (new_cost - current_cost + implementation_cost) * discount_factor
        
        annual_rows.append({
            'year': year,
            'current_scenario_cost': current_cost * discount_factor,
            'new_scenario_cost': new_cost * discount_factor,
            'implementation_cost': implementation_cost * discount_factor,
            'budget_impact': budget_impact,
            'discount_factor': discount_factor
        })
    
    annual_df = pd.DataFrame(annual_rows)
    
    # Calculate cumulative budget impact
    annual_df['cumulative_budget_impact'] = annual_df['budget_impact'].cumsum()
    
    cumulative_df = annual_df[['year', 'cumulative_budget_impact']].copy()
    
    # Cost breakdown by strategy
    cost_breakdown_rows = []
    for strategy in psa.strategies:
        final_share = final_market_shares.get(strategy, 0)
        cost_per_patient = mean_costs.get(strategy, 0)
        annual_cost = final_share * cost_per_patient * population_size
        
        cost_breakdown_rows.append({
            'strategy': strategy,
            'market_share': final_share,
            'cost_per_patient': cost_per_patient,
            'annual_cost': annual_cost,
            'total_cost': annual_cost * time_horizon
        })
    
    cost_breakdown = pd.DataFrame(cost_breakdown_rows)
    
    return BIAResult(
        annual_budget_impact=annual_df,
        cumulative_budget_impact=cumulative_df,
        market_share_evolution=market_shares,
        cost_breakdown=cost_breakdown,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )


def run_bia_analysis(
    psa: PSAData,
    population_size: int,
    time_horizon: int = 5,
    initial_market_shares: Optional[Dict[str, float]] = None,
    final_market_shares: Optional[Dict[str, float]] = None,
    implementation_costs: Optional[Dict[str, float]] = None,
    discount_rate: float = 0.05,
) -> BIAResult:
    """
    Run complete Budget Impact Analysis.
    
    Args:
        psa: PSAData object
        population_size: Eligible population size
        time_horizon: Number of years (default 5):
        initial_market_shares: Initial market shares
        final_market_shares: Final market shares
        implementation_costs: One-time implementation costs
        discount_rate: Annual discount rate
    
    Returns:
        BIAResult with complete analysis
    """
    # Default market shares if not provided
    if initial_market_shares is None:
        # Assume current scenario is all usual care
        initial_market_shares = {psa.config.base: 1.0}
        for strategy in psa.strategies:
            if strategy != psa.config.base:
                initial_market_shares[strategy] = 0.0
    
    if final_market_shares is None:
        # Assume equal distribution in new scenario
        n_strategies = len(psa.strategies)
        final_market_shares = {s: 1.0 / n_strategies for s in psa.strategies}
    
    return calculate_budget_impact(
        psa=psa,
        population_size=population_size,
        time_horizon=time_horizon,
        initial_market_shares=initial_market_shares,
        final_market_shares=final_market_shares,
        implementation_costs=implementation_costs,
        discount_rate=discount_rate
    )


def save_bia_results(
    bia_result: BIAResult,
    output_dir: Path
) -> None:
    """
    Save BIA results to files.
    
    Args:
        bia_result: BIA results
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save annual budget impact
    bia_result.annual_budget_impact.to_csv(
        output_dir / "bia_annual.csv", index=False
    )
    
    # Save cumulative budget impact
    bia_result.cumulative_budget_impact.to_csv(
        output_dir / "bia_cumulative.csv", index=False
    )
    
    # Save market share evolution
    bia_result.market_share_evolution.to_csv(
        output_dir / "bia_market_shares.csv", index=False
    )
    
    # Save cost breakdown
    bia_result.cost_breakdown.to_csv(
        output_dir / "bia_cost_breakdown.csv", index=False
    )
    
    # Save metadata
    import json
    metadata = {
        'perspective': bia_result.perspective,
        'jurisdiction': bia_result.jurisdiction,
        'time_horizon': len(bia_result.annual_budget_impact) - 1,
        'total_budget_impact': float(bia_result.cumulative_budget_impact['cumulative_budget_impact'].iloc[-1])
    }
    
    with open(output_dir / "bia_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)


# Additional BIA functions temporarily commented out due to syntax issues
# These functions need to be fixed to work properly

def calculate_annual_budget_impact(psa: PSAData, years: int, population_size: int = 10000, discount_rate: float = 0.05) -> pd.DataFrame:
    """Calculate annual budget impact table per strategy and year.

    This creates a tidy DataFrame with per-strategy annual costs, discounted costs,
    and scenario comparisons consistent with the rest of the BIA engine.
    """
    # Use a simple equal-split final market share for estimation
    market_shares = calculate_market_share_evolution_from_psa(psa, years)
    mean_costs = psa.table.groupby('strategy')['cost'].mean().to_dict()

    rows = []
    for year in range(years + 1):
        discount = 1 / ((1 + discount_rate) ** year)
        for strategy in psa.strategies:
            ms_row = market_shares[(market_shares['year'] == year) & (market_shares['strategy'] == strategy)]
            market_share = ms_row['market_share'].iloc[0] if not ms_row.empty else 0.0
            mean_cost = mean_costs.get(strategy, 0.0)
            total_annual_cost = market_share * mean_cost * population_size

            rows.append({
                'year': year,
                'strategy': strategy,
                'mean_cost': mean_cost,
                'discounted_cost': total_annual_cost * discount,
                'population_size': population_size,
                'total_annual_cost': total_annual_cost,
                'budget_impact': total_annual_cost,  # For compatibility
                'current_scenario_cost': 0.0,
                'new_scenario_cost': total_annual_cost,
                'perspective': psa.perspective,
                'jurisdiction': psa.jurisdiction
            })

    return pd.DataFrame(rows)


def calculate_cumulative_budget_impact(annual_bia: pd.DataFrame) -> pd.DataFrame:
    """Aggregate annual BIA into cumulative per year and strategy."""
    df = annual_bia.copy()
    df = df.sort_values(['strategy', 'year'])
    df['cumulative_cost'] = df.groupby('strategy')['total_annual_cost'].cumsum()
    df['cumulative_impact'] = df['cumulative_cost']
    # Provide alias column name 'annual_cost' expected by tests
    df = df.rename(columns={'total_annual_cost': 'annual_cost'})
    return df[['year', 'strategy', 'annual_cost', 'cumulative_cost', 'cumulative_impact', 'perspective', 'jurisdiction']]


def calculate_budget_breakdown(psa: PSAData) -> pd.DataFrame:
    """Return a simple budget breakdown by strategy with placeholder categories."""
    mean_costs = psa.table.groupby('strategy')['cost'].mean().to_dict()
    rows = []
    for strategy, mean_cost in mean_costs.items():
        rows.append({
            'strategy': strategy,
            'category': 'Drug Cost',
            'cost': mean_cost * 0.6,
            'total_cost': mean_cost,
            'perspective': psa.perspective,
            'jurisdiction': psa.jurisdiction
        })
        rows.append({
            'strategy': strategy,
            'category': 'Administration Cost',
            'cost': mean_cost * 0.3,
            'total_cost': mean_cost,
            'perspective': psa.perspective,
            'jurisdiction': psa.jurisdiction
        })
        rows.append({
            'strategy': strategy,
            'category': 'Monitoring Cost',
            'cost': mean_cost * 0.1,
            'total_cost': mean_cost,
            'perspective': psa.perspective,
            'jurisdiction': psa.jurisdiction
        })

    return pd.DataFrame(rows)


def calculate_scenario_comparison(psa: PSAData, years: int, scenarios: List[str]) -> pd.DataFrame:
    """Generate a simplistic scenario comparison table across scenarios and strategies."""
    rows = []
    mean_costs = psa.table.groupby('strategy')['cost'].mean().to_dict()
    for scenario in scenarios:
        for strategy, mean_cost in mean_costs.items():
            # Adjust cost by scenario modifier
            modifier = 1.0
            if scenario == 'optimistic':
                modifier = 0.9
            elif scenario == 'pessimistic':
                modifier = 1.1

            rows.append({
                'scenario': scenario,
                'strategy': strategy,
                'adjusted_cost': mean_cost * modifier,
                'total_impact': mean_cost * modifier * years,
                'perspective': psa.perspective,
                'jurisdiction': psa.jurisdiction
            })

    return pd.DataFrame(rows)





def calculate_population_impact(psa: PSAData, years: int, population_size: int = 100000) -> pd.DataFrame:
    """
    Calculate population impact metrics.
    
    Args:
        psa: PSAData object
        years: Time horizon
        population_size: Eligible population size
    
    Returns:
        DataFrame with population impact metrics
    """
    impact_rows = []
    market_shares = calculate_market_share_evolution_from_psa(psa, years)
    market_lookup = market_shares.set_index(['year', 'strategy'])['market_share'].to_dict()
    n_strategies = len(psa.strategies)
    
    for year in range(years + 1):
        for strategy in psa.strategies:
            strategy_data = psa.table[psa.table['strategy'] == strategy]
            
            mean_effect = strategy_data['effect'].mean()
            mean_cost = strategy_data['cost'].mean()
            market_share = market_lookup.get((year, strategy), 1.0 / n_strategies)
            n_patients = population_size * market_share
            
            impact_rows.append({
                'year': year,
                'strategy': strategy,
                'population_size': population_size,
                'market_share': market_share,
                'n_patients': n_patients,
                'mean_cost': mean_cost,
                'mean_effect': mean_effect,
                'total_cost': n_patients * mean_cost,
                'total_effect': n_patients * mean_effect,
                # Backwards-compatible aliases expected by tests
                'mean_qalys': mean_effect,
                'total_qalys': n_patients * mean_effect,
                'perspective': psa.perspective,
                'jurisdiction': psa.jurisdiction
            })
    
    return pd.DataFrame(impact_rows)


def calculate_affordability(
    psa: PSAData, years: int, budget_constraint: float, population_size: int = 100000
) -> pd.DataFrame:
    """
    Calculate affordability metrics.
    
    Args:
        psa: PSAData object
        years: Time horizon
        budget_constraint: Annual budget constraint
        population_size: Eligible population size
    
    Returns:
        DataFrame with affordability analysis
    """
    # Get population impact data which includes patient volumes and total costs
    population_impact = calculate_population_impact(psa, years, population_size)
    
    affordability_rows = []
    budget_capacity = float(budget_constraint)
    
    for strategy in psa.strategies:
        for year in range(1, years + 1):
            # Get the annual cost for this strategy and year from population impact
            year_strategy_data = population_impact[
                (population_impact['year'] == year) & 
                (population_impact['strategy'] == strategy)
            ]
            
            if not year_strategy_data.empty:
                total_annual_cost = year_strategy_data['total_cost'].iloc[0]
                budget_utilization = total_annual_cost / budget_capacity if budget_capacity > 0 else 0.0
                
                affordability_rows.append({
                    'year': year,
                    'strategy': strategy,
                    'budget_impact': float(total_annual_cost),
                    'budget_capacity': budget_capacity,
                    'budget_threshold': budget_capacity,
                    'budget_utilization': float(budget_utilization),
                    'affordable': budget_utilization <= 1.0,
                    'perspective': psa.perspective,
                    'jurisdiction': psa.jurisdiction
                })
    
    return pd.DataFrame(affordability_rows)


def calculate_market_share_evolution_from_psa(psa: PSAData, time_horizon: int) -> pd.DataFrame:
    """
    Calculate market share evolution from PSA data.
    
    Args:
        psa: PSAData object
        time_horizon: Number of years
    
    Returns:
        DataFrame with market share evolution over time
    """
    # Get unique strategies from PSA data
    strategies = psa.table['strategy'].unique()
    
    # Initialize with equal market shares (simplified assumption)
    initial_share = 1.0 / len(strategies)
    initial_shares = {strategy: initial_share for strategy in strategies}
    
    # Simplified final shares - in practice would be based on adoption modeling
    final_shares = {}
    for strategy in strategies:
        if 'ECT' in strategy:
            final_shares[strategy] = 0.3  # ECT maintains share
        elif 'KA' in strategy or 'ketamine' in strategy.lower():
            final_shares[strategy] = 0.4  # Ketamine therapies gain share
        else:
            final_shares[strategy] = 0.1  # Other therapies
    
    # Normalize final shares
    total_final = sum(final_shares.values())
    final_shares = {k: v / total_final for k, v in final_shares.items()}
    
    # Calculate evolution over time (linear adoption)
    market_share_rows = []
    for year in range(time_horizon + 1):
        fraction = year / time_horizon if time_horizon > 0 else 1.0
        
        for strategy in strategies:
            initial = initial_shares.get(strategy, 0)
            final = final_shares.get(strategy, 0)
            current_share = initial + (final - initial) * fraction
            
            market_share_rows.append({
                'year': year,
                'strategy': strategy,
                'market_share': current_share
            })
    
    return pd.DataFrame(market_share_rows)
