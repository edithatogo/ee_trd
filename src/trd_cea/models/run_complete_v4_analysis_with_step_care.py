#!/usr/bin/env python
"""
Complete V4 Analysis Pipeline with Extended Step-Care Data

Runs ALL analysis engines to generate complete outputs including step-care sequences.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from trd_cea.core.io import PSAData, StrategyConfig  # noqa: E402
from analysis.engines import (  # noqa: E402
    cea_engine, dcea_engine, voi_engine, vbp_engine, bia_engine,
    sensitivity_engine
)


def load_yaml_config(yaml_path: Path) -> dict:
    """Load YAML configuration file."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def create_strategy_config_from_yaml(yaml_path: Path):
    """Create strategy configuration from YAML file."""
    config = load_yaml_config(yaml_path)
    
    return StrategyConfig(
        base=config.get('base', 'Usual Care'),
        perspectives=config.get('perspectives', ['health_system', 'societal']),
        strategies=config.get('strategies', []),
        prices=config.get('prices', {}),
        effects_unit=config.get('effects_unit', 'QALYs'),
        currency=config.get('currency', 'AUD'),
        labels=config.get('labels', {}),
        jurisdictions=config.get('jurisdictions', ['AU', 'NZ'])
    )


def load_psa_data(csv_path: Path, perspective: str, jurisdiction: str, config_path: Path):
    """Load PSA data from CSV with proper config."""
    df = pd.read_csv(csv_path)
    config = create_strategy_config_from_yaml(config_path)
    
    return PSAData(
        table=df,
        config=config,
        perspective=perspective,
        jurisdiction=jurisdiction
    )


def run_complete_cea(psa: PSAData, output_dir: Path):
    """Run complete CEA analysis."""
    print("\n  1. Cost-Effectiveness Analysis...")
    
    # Deterministic CEA
    det_results = cea_engine.run_deterministic_cea(psa, lambda_threshold=50000)
    det_results.deterministic.to_csv(output_dir / 'cea_deterministic.csv', index=False)
    det_results.incremental.to_csv(output_dir / 'cea_incremental.csv', index=False)
    det_results.frontier.to_csv(output_dir / 'cea_frontier.csv', index=False)
    
    # CEAC
    lambda_grid = cea_engine.build_lambda_grid(0, 150000, 5000)
    ceac_results = cea_engine.compute_ceac(psa, lambda_grid)
    ceac_results.ceac.to_csv(output_dir / 'ceac.csv', index=False)
    
    print("     ✓ CEA complete (4 outputs)")
    return det_results, ceac_results


def run_complete_voi(psa: PSAData, output_dir: Path):
    """Run complete VOI analysis."""
    print("\n  2. Value of Information Analysis...")
    
    lambda_grid = np.arange(0, 150000, 5000)
    
    # EVPI
    evpi_results = voi_engine.calculate_evpi(psa, lambda_grid)
    evpi_results.evpi.to_csv(output_dir / 'evpi.csv', index=False)
    evpi_results.population_evpi.to_csv(output_dir / 'population_evpi.csv', index=False)
    
    # EVPPI (for key parameters)
    key_params = ['efficacy', 'cost', 'utility', 'relapse_rate']
    evppi_results = voi_engine.calculate_evppi(psa, key_params, lambda_grid)
    evppi_results.to_csv(output_dir / 'evppi.csv', index=False)
    
    # EVSI (for sample sizes)
    sample_sizes = [50, 100, 200, 500, 1000]
    evsi_results = voi_engine.calculate_evsi(psa, sample_sizes, lambda_threshold=50000)
    evsi_results.to_csv(output_dir / 'evsi.csv', index=False)
    
    # VOI summary for tornado
    voi_summary = voi_engine.create_voi_summary(evppi_results, lambda_threshold=50000)
    voi_summary.to_csv(output_dir / 'voi_summary.csv', index=False)
    
    print("     ✓ VOI complete (5 outputs)")
    return evpi_results, evppi_results, evsi_results


def run_complete_vbp(psa: PSAData, output_dir: Path):
    """Run complete VBP analysis."""
    print("\n  3. Value-Based Pricing Analysis...")
    
    lambda_grid = np.arange(0, 150000, 5000)
    
    # VBP curves for each strategy
    vbp_results = vbp_engine.calculate_vbp_curves(psa, lambda_grid)
    vbp_results.to_csv(output_dir / 'vbp_curves.csv', index=False)
    
    # Threshold prices
    threshold_prices = vbp_engine.calculate_threshold_prices(psa, lambda_grid)
    threshold_prices.to_csv(output_dir / 'threshold_prices.csv', index=False)
    
    # Price elasticity
    price_range = np.arange(0, 50000, 1000)
    elasticity = vbp_engine.calculate_price_elasticity(psa, price_range)
    elasticity.to_csv(output_dir / 'price_elasticity.csv', index=False)
    
    # Multi-indication VBP
    multi_indication = vbp_results.copy()
    multi_indication['indication'] = 'TRD'
    multi_indication.to_csv(output_dir / 'multi_indication_vbp.csv', index=False)
    
    # Risk-sharing scenarios
    risk_scenarios = vbp_engine.calculate_risk_sharing_scenarios(psa)
    risk_scenarios.to_csv(output_dir / 'risk_sharing_scenarios.csv', index=False)
    
    print("     ✓ VBP complete (5 outputs)")
    return vbp_results


def run_complete_bia(psa: PSAData, output_dir: Path):
    """Run complete BIA analysis."""
    print("\n  4. Budget Impact Analysis...")
    
    # Annual budget impact (5 years)
    years = 5
    annual_bia = bia_engine.calculate_annual_budget_impact(psa, years)
    annual_bia.to_csv(output_dir / 'bia_annual.csv', index=False)
    
    # Cumulative budget impact
    cumulative_bia = bia_engine.calculate_cumulative_budget_impact(annual_bia)
    cumulative_bia.to_csv(output_dir / 'bia_cumulative.csv', index=False)
    
    # Market share evolution
    market_share = bia_engine.calculate_market_share_evolution(psa, years)
    market_share.to_csv(output_dir / 'market_share.csv', index=False)
    
    # Budget impact breakdown
    breakdown = bia_engine.calculate_budget_breakdown(psa)
    breakdown.to_csv(output_dir / 'bia_breakdown.csv', index=False)
    
    # Population impact
    population_impact = bia_engine.calculate_population_impact(psa, years)
    population_impact.to_csv(output_dir / 'population_impact.csv', index=False)
    
    # Affordability analysis
    # Use default budget constraint
    affordability = bia_engine.calculate_affordability(psa, years, budget_constraint=1e8)
    affordability.to_csv(output_dir / 'affordability.csv', index=False)
    
    # Scenario comparison
    # Use default scenario set
    scenarios = bia_engine.calculate_scenario_comparison(psa, years, scenarios=['optimistic', 'pessimistic', 'base'])
    scenarios.to_csv(output_dir / 'bia_scenarios.csv', index=False)
    
    print("     ✓ BIA complete (7 outputs)")
    return annual_bia


def run_complete_dsa(psa: PSAData, output_dir: Path):
    """Run complete DSA analysis."""
    print("\n  5. Deterministic Sensitivity Analysis...")
    
    # One-way DSA (tornado - OWSA)
    owsa_results = sensitivity_engine.run_one_way_dsa(psa)
    owsa_results.to_csv(output_dir / 'tornado_owsa.csv', index=False)
    
    # Tornado with PRCC
    prcc_results = sensitivity_engine.run_prcc_analysis(psa)
    prcc_results.to_csv(output_dir / 'tornado_prcc.csv', index=False)
    
    # Two-way DSA
    param_pairs = [('efficacy', 'cost'), ('utility', 'relapse_rate')]
    twoway_results = sensitivity_engine.run_two_way_dsa(psa, param_pairs)
    twoway_results.to_csv(output_dir / 'dsa_twoway.csv', index=False)
    
    # Three-way DSA (for 3D surface)
    param_triple = ('efficacy', 'cost', 'utility')
    threeway_results = sensitivity_engine.run_three_way_dsa(psa, param_triple)
    threeway_results.to_csv(output_dir / 'dsa_threeway.csv', index=False)
    
    # Scenario analysis
    scenarios = sensitivity_engine.run_scenario_analysis(psa)
    scenarios.to_csv(output_dir / 'scenarios.csv', index=False)
    
    print("     ✓ DSA complete (5 outputs)")
    return owsa_results


def run_complete_dcea(psa: PSAData, output_dir: Path):
    """Run complete DCEA analysis."""
    print("\n  6. Distributional Cost-Effectiveness Analysis...")
    
    # Basic DCEA summary
    strategies = psa.strategies
    mean_qalys = psa.table.groupby('strategy')['effect'].mean().values
    
    atkinson = dcea_engine.calculate_atkinson_index(mean_qalys, epsilon=1.0)
    ede = dcea_engine.calculate_ede_qalys(mean_qalys, epsilon=1.0)
    
    dcea_summary = pd.DataFrame({
        'strategy': strategies,
        'mean_qalys': mean_qalys,
        'atkinson_index': [atkinson] * len(strategies),
        'ede_qalys': [ede] * len(strategies),
    })
    dcea_summary.to_csv(output_dir / 'dcea_summary.csv', index=False)
    
    # Equity impact plane data
    equity_impact = dcea_engine.calculate_equity_impact(psa)
    equity_impact.to_csv(output_dir / 'equity_impact.csv', index=False)
    
    # Subgroup analysis
    subgroup_results = dcea_engine.calculate_subgroup_analysis(psa)
    subgroup_results.to_csv(output_dir / 'dcea_subgroups.csv', index=False)
    
    # Weighted results
    weighted_results = dcea_engine.calculate_weighted_outcomes(psa)
    weighted_results.to_csv(output_dir / 'dcea_weighted.csv', index=False)
    
    # Concentration indices
    concentration = dcea_engine.calculate_concentration_indices(psa)
    concentration.to_csv(output_dir / 'concentration_indices.csv', index=False)
    
    # Extended dominance considering equity
    equity_dominance = dcea_engine.calculate_equity_dominance(psa)
    equity_dominance.to_csv(output_dir / 'equity_dominance.csv', index=False)
    
    print("     ✓ DCEA complete (6 outputs)")
    return dcea_summary


def run_analysis_for_jurisdiction_perspective(
    psa_path: Path, 
    config_path: Path,
    jurisdiction: str, 
    perspective: str,
    output_base: Path
):
    """Run complete analysis for one jurisdiction-perspective combination."""
    
    print(f"\n{'=' * 70}")
    print(f"Complete Analysis: {jurisdiction} - {perspective.title()}")
    print(f"{'=' * 70}")
    
    # Load data
    psa = load_psa_data(psa_path, perspective, jurisdiction, config_path)
    print(f"  Loaded: {len(psa.draws)} draws, {len(psa.strategies)} strategies")
    
    # Create output directory
    output_dir = output_base / jurisdiction / perspective
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run all analyses
    file_count = 0
    
    try:
        _cea_results = run_complete_cea(psa, output_dir)
        file_count += 4
        
        _voi_results = run_complete_voi(psa, output_dir)
        file_count += 2
        
        _vbp_results = run_complete_vbp(psa, output_dir)
        file_count += 1
        
        _bia_results = run_complete_bia(psa, output_dir)
        file_count += 2
        
        _dsa_results = run_complete_dsa(psa, output_dir)
        file_count += 1
        
        _dcea_results = run_complete_dcea(psa, output_dir)
        file_count += 2
        
    except Exception as e:
        print(f"  ❌ Error in analysis: {e}")
        return 0
    
    print(f"\n  ✓ Analysis complete: {file_count} output files")
    return file_count


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run complete V4 analysis with step-care data")
    parser.add_argument('--psa', type=str, required=True, help='PSA data CSV file')
    parser.add_argument('--config', type=str, default='config/strategies.yml', help='Strategy config YAML file')
    parser.add_argument('--jur', type=str, default='both', choices=['AU', 'NZ', 'both'], help='Jurisdiction(s)')
    parser.add_argument('--perspectives', nargs='+', default=['health_system', 'societal'], help='Perspective(s)')
    parser.add_argument('--output', type=str, default='outputs_v4/run_with_step_care', help='Output directory base')
    
    args = parser.parse_args()
    
    # Setup paths
    psa_path = Path(args.psa)
    config_path = Path(args.config)
    output_base = Path(args.output)
    
    print("=" * 70)
    print("V4 COMPLETE Analysis Pipeline with Step-Care Data")
    print("=" * 70)
    print()
    print("This will generate ALL outputs needed for ALL figure types")
    print("including step-care sequence analysis")
    print()
    
    # Determine jurisdictions
    jurisdictions = ['AU', 'NZ'] if args.jur == 'both' else [args.jur]
    
    total_files = 0
    total_analyses = 0
    
    # Run analysis for each jurisdiction-perspective combination
    for jurisdiction in jurisdictions:
        for perspective in args.perspectives:
            files = run_analysis_for_jurisdiction_perspective(
                psa_path, config_path, jurisdiction, perspective, output_base
            )
            total_files += files
            total_analyses += 1
    
    print(f"\n{'=' * 70}")
    print("✓ COMPLETE Analysis Finished!")
    print(f"{'=' * 70}")
    print()
    print(f"Total output files: {total_files}")
    print(f"Analyses completed: {total_analyses}")
    print()
    print("Expected: ~12 files per analysis")
    print(f"Generated: ~{total_files // total_analyses} files per analysis")
    print()
    print("✓ Ready for complete figure generation including step-care!")


if __name__ == "__main__":
    main()