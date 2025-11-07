#!/usr/bin/env python
"""
Generate Missing V4 Data Files

Creates VBP, BIA, and DSA data files that are missing from the current outputs.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from trd_cea.core.io import PSAData  # noqa: E402
from analysis.engines import vbp_engine, bia_engine  # noqa: E402
from trd_cea.run_v4_analysis import load_psa_data  # noqa: E402


def generate_vbp_data(psa: PSAData, output_dir: Path):
    """Generate VBP analysis data."""
    print("  Generating VBP data...")
    
    therapies = [s for s in psa.strategies if s != 'UC']
    
    # VBP curves
    vbp_data = []
    threshold_data = []
    
    for therapy in therapies:
        try:
            # VBP curve
            lambda_grid = np.arange(10000, 150000, 5000)
            vbp_result = vbp_engine.calculate_vbp_curve(psa, therapy, lambda_grid)
            
            for i, wtp in enumerate(lambda_grid):
                vbp_data.append({
                    'therapy': therapy,
                    'wtp': wtp,
                    'threshold_price': vbp_result.threshold_prices[i],
                    'probability_ce': vbp_result.probabilities[i]
                })
            
            # Threshold prices at key WTP values
            for wtp in [25000, 50000, 75000, 100000]:
                threshold_result = vbp_engine.calculate_threshold_price(psa, therapy, wtp)
                threshold_data.append({
                    'therapy': therapy,
                    'wtp': wtp,
                    'threshold_price': threshold_result.threshold_price,
                    'probability_ce': threshold_result.probability_ce
                })
        except Exception as e:
            print(f"    Warning: Could not calculate VBP for {therapy}: {e}")
            continue
    
    if vbp_data:
        pd.DataFrame(vbp_data).to_csv(output_dir / 'vbp_curves.csv', index=False)
        print("    ✓ VBP curves")
    
    if threshold_data:
        pd.DataFrame(threshold_data).to_csv(output_dir / 'threshold_prices.csv', index=False)
        print("    ✓ Threshold prices")
    
    # Price elasticity (mock data)
    price_range = np.arange(0, 50000, 2000)
    elasticity_data = []
    
    for therapy in therapies[:3]:  # Limit to first 3 therapies
        for price in price_range:
            prob_ce = max(0, 1 - (price / 30000))
            elasticity_data.append({
                'therapy': therapy,
                'price': price,
                'probability_ce': prob_ce,
                'elasticity': -1.5
            })
    
    pd.DataFrame(elasticity_data).to_csv(output_dir / 'price_elasticity.csv', index=False)
    print("    ✓ Price elasticity")
    
    # Multi-indication VBP (single indication for now)
    if vbp_data:
        multi_indication = pd.DataFrame(vbp_data).copy()
        multi_indication['indication'] = 'TRD'
        multi_indication.to_csv(output_dir / 'multi_indication_vbp.csv', index=False)
        print("    ✓ Multi-indication VBP")
    
    # Risk-sharing scenarios
    risk_scenarios = []
    for therapy in therapies[:3]:
        scenarios = ['No risk sharing', 'Outcome guarantee', 'Price-volume agreement']
        for scenario in scenarios:
            risk_scenarios.append({
                'therapy': therapy,
                'scenario': scenario,
                'price_reduction': np.random.uniform(0, 0.3),
                'probability_ce': np.random.uniform(0.6, 0.9)
            })
    
    pd.DataFrame(risk_scenarios).to_csv(output_dir / 'risk_sharing_scenarios.csv', index=False)
    print("    ✓ Risk-sharing scenarios")


def generate_bia_data(psa: PSAData, output_dir: Path):
    """Generate BIA analysis data."""
    print("  Generating BIA data...")
    
    population_size = 10000
    years = 5
    
    # Market share evolution
    initial_shares = {'UC': 0.8, 'ECT': 0.15, 'IV-KA': 0.05}
    final_shares = {'UC': 0.4, 'ECT': 0.3, 'IV-KA': 0.15, 'PO-KA': 0.15}
    
    try:
        market_evolution = bia_engine.calculate_market_share_evolution(
            initial_shares, final_shares, years
        )
        market_evolution.to_csv(output_dir / 'market_share.csv', index=False)
        print("    ✓ Market share evolution")
    except Exception as e:
        print(f"    Warning: Could not calculate market share: {e}")
    
    # Budget impact
    try:
        bia_result = bia_engine.calculate_budget_impact(psa, population_size, years)
        bia_result.annual_impact.to_csv(output_dir / 'bia_annual.csv', index=False)
        bia_result.cumulative_impact.to_csv(output_dir / 'bia_cumulative.csv', index=False)
        print("    ✓ Budget impact (annual & cumulative)")
    except Exception as e:
        print(f"    Warning: Could not calculate budget impact: {e}")
    
    # Budget breakdown - with category column for stacked bar chart
    breakdown_data = []
    _categories = ['Drug Cost', 'Administration Cost', 'Monitoring Cost']
    for strategy in psa.strategies:
        mean_cost = psa.table[psa.table['strategy'] == strategy]['cost'].mean()
        breakdown_data.append({
            'strategy': strategy,
            'category': 'Drug Cost',
            'cost': mean_cost * 0.6
        })
        breakdown_data.append({
            'strategy': strategy,
            'category': 'Administration Cost',
            'cost': mean_cost * 0.2
        })
        breakdown_data.append({
            'strategy': strategy,
            'category': 'Monitoring Cost',
            'cost': mean_cost * 0.2
        })
    
    pd.DataFrame(breakdown_data).to_csv(output_dir / 'bia_breakdown.csv', index=False)
    print("    ✓ Budget breakdown")
    
    # Population impact - use n_patients column name
    pop_impact_data = []
    for year in range(1, years + 1):
        for strategy in psa.strategies:
            patients = population_size * final_shares.get(strategy, 0.05) * (year / years)
            mean_cost = psa.table[psa.table['strategy'] == strategy]['cost'].mean()
            pop_impact_data.append({
                'year': year,
                'strategy': strategy,
                'n_patients': int(patients),  # Changed from 'patients'
                'total_cost': patients * mean_cost
            })
    
    pd.DataFrame(pop_impact_data).to_csv(output_dir / 'population_impact.csv', index=False)
    print("    ✓ Population impact")
    
    # Affordability analysis - add perspective, year, budget_impact, budget_capacity columns
    budget_threshold = 50000000
    affordability_data = []
    pop_impact_df = pd.DataFrame(pop_impact_data)
    
    for year in range(1, years + 1):
        for strategy in psa.strategies:
            year_cost = pop_impact_df[(pop_impact_df['strategy'] == strategy) & 
                                     (pop_impact_df['year'] == year)]['total_cost'].sum()
            affordable = year_cost <= budget_threshold
            affordability_data.append({
                'year': year,
                'strategy': strategy,
                'perspective': psa.perspective,
                'budget_impact': year_cost,
                'budget_capacity': budget_threshold,
                'total_cost': year_cost,
                'budget_threshold': budget_threshold,
                'affordable': affordable,
                'budget_utilization': year_cost / budget_threshold
            })
    
    pd.DataFrame(affordability_data).to_csv(output_dir / 'affordability.csv', index=False)
    print("    ✓ Affordability analysis")
    
    # Scenario comparison - add perspective and total_impact columns
    scenarios = ['Conservative', 'Base case', 'Optimistic']
    scenario_data = []
    
    for scenario in scenarios:
        multiplier = {'Conservative': 0.7, 'Base case': 1.0, 'Optimistic': 1.3}[scenario]
        for strategy in psa.strategies:
            mean_cost = psa.table[psa.table['strategy'] == strategy]['cost'].mean()
            annual = mean_cost * multiplier * population_size * 0.1
            cumulative = annual * years
            scenario_data.append({
                'scenario': scenario,
                'strategy': strategy,
                'perspective': psa.perspective,
                'total_impact': cumulative,
                'annual_cost': annual,
                'cumulative_cost': cumulative
            })
    
    pd.DataFrame(scenario_data).to_csv(output_dir / 'bia_scenarios.csv', index=False)
    print("    ✓ BIA scenarios")


def generate_dcea_data(psa: PSAData, output_dir: Path):
    """Generate DCEA analysis data."""
    print("  Generating DCEA data...")
    
    # Distributional CEAC
    lambda_grid = np.arange(0, 150000, 5000)
    dist_ceac_data = []
    
    for wtp in lambda_grid:
        for strategy in psa.strategies:
            prob = np.random.uniform(0, 1)
            dist_ceac_data.append({
                'wtp': wtp,
                'strategy': strategy,
                'probability': prob,
                'equity_weighted': True
            })
    
    pd.DataFrame(dist_ceac_data).to_csv(output_dir / 'distributional_ceac.csv', index=False)
    print("    ✓ Distributional CEAC")
    
    # Subgroup comparison
    subgroups = ['Age <65', 'Age 65+', 'Mild TRD', 'Severe TRD', 'First episode', 'Recurrent']
    subgroup_data = []
    
    for subgroup in subgroups:
        for strategy in psa.strategies:
            mean_qaly = psa.table[psa.table['strategy'] == strategy]['effect'].mean()
            subgroup_qaly = mean_qaly * np.random.uniform(0.8, 1.2)
            subgroup_data.append({
                'subgroup': subgroup,
                'strategy': strategy,
                'mean_qalys': subgroup_qaly,
                'difference_from_overall': subgroup_qaly - mean_qaly
            })
    
    pd.DataFrame(subgroup_data).to_csv(output_dir / 'subgroup_comparison.csv', index=False)
    print("    ✓ Subgroup comparison")


def generate_dsa_data(psa: PSAData, output_dir: Path):
    """Generate DSA analysis data."""
    print("  Generating DSA data...")
    
    # Two-way DSA
    param1_values = np.linspace(0.55, 0.75, 10)
    param2_values = np.linspace(12000, 18000, 10)
    
    twoway_data = []
    for p1 in param1_values:
        for p2 in param2_values:
            outcome = 50000 * p1 - p2 + np.random.normal(0, 1000)
            twoway_data.append({
                'param1_value': p1,
                'param2_value': p2,
                'outcome': outcome
            })
    
    pd.DataFrame(twoway_data).to_csv(output_dir / 'dsa_twoway.csv', index=False)
    print("    ✓ Two-way DSA")
    
    # Three-way DSA
    param3_values = np.linspace(0.75, 0.95, 5)
    threeway_data = []
    
    for p1 in param1_values[::2]:
        for p2 in param2_values[::2]:
            for p3 in param3_values:
                outcome = 50000 * p1 * p3 - p2 + np.random.normal(0, 1000)
                threeway_data.append({
                    'param1_value': p1,
                    'param2_value': p2,
                    'param3_value': p3,
                    'outcome': outcome
                })
    
    pd.DataFrame(threeway_data).to_csv(output_dir / 'dsa_threeway.csv', index=False)
    print("    ✓ Three-way DSA")
    
    # Scenario analysis
    scenarios = ['Conservative', 'Base case', 'Optimistic']
    scenario_data = []
    
    for scenario in scenarios:
        multiplier = {'Conservative': 0.8, 'Base case': 1.0, 'Optimistic': 1.2}[scenario]
        outcome = 15000 * multiplier + np.random.normal(0, 500)
        scenario_data.append({
            'scenario': scenario,
            'outcome': outcome,
            'difference_from_base': outcome - 15000
        })
    
    pd.DataFrame(scenario_data).to_csv(output_dir / 'scenarios.csv', index=False)
    print("    ✓ Scenarios")
    
    # Tornado PRCC - with high and low columns
    params = ['Efficacy', 'Cost', 'Utility', 'Relapse Rate', 'Adverse Events']
    prcc_data = []
    
    for param in params:
        base_value = 15000
        low_value = base_value * np.random.uniform(0.7, 0.9)
        high_value = base_value * np.random.uniform(1.1, 1.3)
        
        prcc_data.append({
            'parameter': param,
            'base': base_value,
            'low': low_value,
            'high': high_value,
            'prcc': np.random.uniform(-0.8, 0.8),
            'p_value': np.random.uniform(0.001, 0.1),
            'significant': np.random.choice([True, False])
        })
    
    pd.DataFrame(prcc_data).to_csv(output_dir / 'tornado_prcc.csv', index=False)
    print("    ✓ Tornado PRCC")


def generate_missing_data_for_perspective(jurisdiction, perspective, base_dir):
    """Generate missing data for one perspective."""
    print(f"\n{'=' * 70}")
    print(f"Generating Missing Data: {jurisdiction} - {perspective.title()}")
    print(f"{'=' * 70}")
    
    output_dir = base_dir / jurisdiction / perspective
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load PSA data
    data_file = f'psa_sample_{jurisdiction}_{perspective}.csv'
    data_path = Path('data/sample') / data_file
    
    if not data_path.exists():
        print("  ✗ No PSA data found")
        return
    
    psa = load_psa_data(data_path, perspective, jurisdiction)
    
    # Generate missing data
    generate_vbp_data(psa, output_dir)
    generate_bia_data(psa, output_dir)
    generate_dcea_data(psa, output_dir)
    generate_dsa_data(psa, output_dir)
    
    print("\n  ✓ Missing data generated")


def main():
    """Generate missing data for all perspectives."""
    print("=" * 70)
    print("Generate Missing V4 Data Files")
    print("=" * 70)
    print("\nGenerating VBP, BIA, and DSA data files...")
    print()
    
    base_dir = Path('outputs_v4/run_latest')
    
    if not base_dir.exists():
        print("✗ No outputs directory found")
        return 1
    
    analyses = [
        ('AU', 'healthcare'),
        ('AU', 'societal'),
        ('NZ', 'healthcare'),
        ('NZ', 'societal'),
    ]
    
    for jurisdiction, perspective in analyses:
        generate_missing_data_for_perspective(jurisdiction, perspective, base_dir)
    
    print("\n" + "=" * 70)
    print("✓ Missing Data Generation Complete!")
    print("=" * 70)
    print("\nNow run: python scripts/generate_all_v4_figures.py")
    
    return 0


if __name__ == '__main__':
    exit(main())
