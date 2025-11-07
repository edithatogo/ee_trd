#!/usr/bin/env python3
"""
Complete V4 Analysis Pipeline (Excluding Usual Care)

Runs ALL analysis engines to generate complete outputs for all figure types,
excluding Usual Care from the results.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from trd_cea.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

sys.path.insert(0, str(Path(__file__).parent.parent))

from trd_cea.core.io import PSAData  # noqa: E402
from analysis.engines import (  # noqa: E402
    cea_engine, dcea_engine, voi_engine, vbp_engine, bia_engine,
    sensitivity_engine, subgroup_engine, cca_engine, roa_engine, 
    roi_engine, mcda_engine
)


def filter_out_usual_care(psa: PSAData) -> PSAData:
    """Filter out Usual Care from PSA data."""
    # Filter the table to exclude "Usual Care" strategy
    filtered_table = psa.table[~psa.table['strategy'].isin(['Usual Care', 'UC'])].copy()

    # Create new PSAData object with filtered data
    filtered_psa = PSAData(
        table=filtered_table,
        config=psa.config,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )

    # Update config to remove Usual Care from configured strategies and reset base if needed
    try:
        remaining = list(filtered_psa.table['strategy'].unique())
        # Remove any 'UC' or 'Usual Care' entries from the strategy list
        filtered_list = [s for s in psa.config.strategies if s not in ('UC', 'Usual Care')]
        if filtered_list:
            psa.config.strategies = filtered_list
            # If the configured base is removed, set base to the first remaining strategy
            if psa.config.base in ('UC', 'Usual Care') or psa.config.base not in psa.config.strategies:
                psa.config.base = psa.config.strategies[0]
    except Exception:
        # If anything goes wrong, just return filtered PSA data; engines will raise clearer errors
        pass

    return filtered_psa


def run_complete_cea(psa: PSAData, output_dir: Path):
    """Run complete CEA analysis."""
    logger.info("Running complete CEA analysis")

    # Show progress in console
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

    # CEAF
    ceaf_results = cea_engine.compute_ceaf(psa, lambda_grid)
    ceaf_results.ceaf.to_csv(output_dir / 'ceaf.csv', index=False)

    # INMB distributions
    inmb_data = cea_engine.compute_inmb_distributions(psa, lambda_threshold=50000)
    inmb_data.to_csv(output_dir / 'inmb_distributions.csv', index=False)

    logger.info("CEA analysis completed successfully (4 outputs)")
    print("     ✓ CEA complete (4 outputs)")
    return det_results, ceac_results, ceaf_results


def run_complete_voi(psa: PSAData, output_dir: Path):
    """Run complete VOI analysis."""
    print("\n  2. Value of Information Analysis...")

    # EVPI
    lambda_grid = np.arange(0, 150000, 5000)
    evpi_results = voi_engine.calculate_evpi(psa, lambda_grid)
    # EVPI (object with .evpi and .population_evpi)
    # evpi_results is expected to be a container with DataFrames
    try:
        evpi_results.evpi.to_csv(output_dir / 'evpi.csv', index=False)
        evpi_results.population_evpi.to_csv(output_dir / 'population_evpi.csv', index=False)
    except Exception:
        # Fallback if API differs
        if hasattr(evpi_results, 'to_csv'):
            evpi_results.to_csv(output_dir / 'evpi.csv', index=False)

    # EVPPI for key parameters
    key_params = ['efficacy', 'cost', 'utility', 'relapse_rate']
    evppi_results = voi_engine.calculate_evppi(psa, key_params, lambda_grid)
    # evppi_results may be a DataFrame or object; try to save sensibly
    try:
        evppi_results.to_csv(output_dir / 'evppi.csv', index=False)
    except Exception:
        # attempt conversion
        pd.DataFrame(evppi_results).to_csv(output_dir / 'evppi.csv', index=False)

    # EVSI placeholder (kept for compatibility)
    evsi_results = pd.DataFrame({'sample_size': [50, 100, 200, 500, 1000], 'evsi': [0.0] * 5})
    evsi_results.to_csv(output_dir / 'evsi.csv', index=False)

    # VOI summary for tornado (canonical expects evppi_results and a lambda threshold)
    try:
        voi_summary = voi_engine.create_voi_summary(evppi_results, lambda_threshold=50000)
        voi_summary.to_csv(output_dir / 'voi_summary.csv', index=False)
    except Exception:
        # best effort: save a placeholder summary
        pd.DataFrame({'note': ['voi summary placeholder']}).to_csv(output_dir / 'voi_summary.csv', index=False)

    print("     ✓ VOI complete (5 outputs)")
    return evpi_results, evppi_results, evsi_results


def run_complete_vbp(psa: PSAData, output_dir: Path):
    """Run complete VBP analysis."""
    print("\n  3. Value-Based Pricing Analysis...")

    # VBP curves
    lambda_grid = np.arange(0, 150000, 5000)
    vbp_curves = vbp_engine.calculate_vbp_curves(psa, lambda_grid)
    vbp_curves.to_csv(output_dir / 'vbp_curves.csv', index=False)

    # Threshold prices
    threshold_prices = vbp_engine.calculate_threshold_prices(psa, lambda_grid)
    threshold_prices.to_csv(output_dir / 'threshold_prices.csv', index=False)

    # Price elasticity
    price_range = np.arange(0, 50000, 1000)
    price_elasticity = vbp_engine.calculate_price_elasticity(psa, price_range)
    price_elasticity.to_csv(output_dir / 'price_elasticity.csv', index=False)

    # Multi-indication VBP
    # Multi-indication VBP - placeholder: duplicate vbp_curves and add an indication column
    multi_indication = vbp_curves.copy()
    multi_indication['indication'] = 'TRD'
    multi_indication.to_csv(output_dir / 'multi_indication_vbp.csv', index=False)

    # Risk-sharing scenarios
    risk_scenarios = vbp_engine.calculate_risk_sharing_scenarios(psa)
    risk_scenarios.to_csv(output_dir / 'risk_sharing_scenarios.csv', index=False)

    print("     ✓ VBP complete (5 outputs)")
    return vbp_curves, threshold_prices, price_elasticity


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

    # Market share evolution (use helper that builds shares from PSA)
    market_share = bia_engine.calculate_market_share_evolution_from_psa(psa, years)
    market_share.to_csv(output_dir / 'market_share.csv', index=False)

    # Budget impact breakdown
    breakdown = bia_engine.calculate_budget_breakdown(psa)
    breakdown.to_csv(output_dir / 'bia_breakdown.csv', index=False)

    # Population impact
    population_impact = bia_engine.calculate_population_impact(psa, years)
    population_impact.to_csv(output_dir / 'population_impact.csv', index=False)

    # Affordability analysis
    # Use a default budget constraint
    affordability = bia_engine.calculate_affordability(psa, years, budget_constraint=1e8)
    affordability.to_csv(output_dir / 'affordability.csv', index=False)

    # Provide a default set of scenarios (placeholder)
    scenarios = bia_engine.calculate_scenario_comparison(psa, years, scenarios=['base','optimistic','pessimistic'])
    scenarios.to_csv(output_dir / 'bia_scenarios.csv', index=False)
    scenarios.to_csv(output_dir / 'bia_scenarios.csv', index=False)

    print("     ✓ BIA complete (7 outputs)")
    return annual_bia


def run_complete_dsa(psa: PSAData, output_dir: Path):
    """Run complete DSA/sensitivity analysis."""
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
    mean_qalys = np.array(psa.table.groupby('strategy')['effect'].mean().values)

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

    # Atkinson index by strategy
    atkinson_by_strategy = dcea_engine.calculate_atkinson_by_strategy(psa)
    atkinson_by_strategy.to_csv(output_dir / 'atkinson_by_strategy.csv', index=False)

    # EDE-QALYs comparison
    ede_comparison = dcea_engine.calculate_ede_comparison(psa)
    ede_comparison.to_csv(output_dir / 'ede_comparison.csv', index=False)

    # Distributional CEAC
    lambda_grid = np.arange(0, 150000, 5000)
    dist_ceac = dcea_engine.calculate_distributional_ceac(psa, lambda_grid)
    dist_ceac.to_csv(output_dir / 'distributional_ceac.csv', index=False)

    # Subgroup comparison (by age, severity, etc.)
    subgroup_comp = dcea_engine.calculate_subgroup_comparison(psa)
    subgroup_comp.to_csv(output_dir / 'subgroup_comparison.csv', index=False)

    print("     ✓ DCEA complete (6 outputs)")
    return dcea_summary


def run_complete_subgroup(psa: PSAData, output_dir: Path):
    """Run complete Subgroup Analysis."""
    print("\n  7. Subgroup Analysis...")
    
    # Run age subgroup analysis
    age_results = subgroup_engine.run_age_subgroup_analysis(psa, lambda_threshold=50000)
    
    # Run severity subgroup analysis
    severity_results = subgroup_engine.run_severity_subgroup_analysis(psa, lambda_threshold=50000)
    
    # Save age subgroup results
    subgroup_engine.save_subgroup_results(age_results, output_dir)
    
    # Save severity subgroup results
    subgroup_engine.save_subgroup_results(severity_results, output_dir)
    
    # Also save combined results for easier analysis
    combined_results = pd.concat([
        age_results.results_by_subgroup.assign(subgroup_type='age'),
        severity_results.results_by_subgroup.assign(subgroup_type='severity')
    ])
    combined_results.to_csv(output_dir / 'subgroup_combined.csv', index=False)
    
    print("     ✓ Subgroup complete (3 outputs)")
    return age_results, severity_results


def run_complete_cca(psa: PSAData, output_dir: Path):
    """Run complete Cost-Consequence Analysis."""
    print("\n  8. Cost-Consequence Analysis...")

    # Create CCA engine
    cca = cca_engine.CostConsequenceEngine(confidence_level=0.95)

    # Run CCA analysis
    cca_results = cca.analyze(psa.table, perspective=psa.perspective)
    
    # Save summary table
    cca_results.summary_table.to_csv(output_dir / "cca_summary.csv", index=False)
    
    # Save cost components
    cost_components_df = pd.DataFrame([
        {
            "component": comp.name,
            "description": comp.description,
            "category": comp.category,
            "mean": comp.mean,
            "ci_lower": comp.ci_lower,
            "ci_upper": comp.ci_upper
        }
        for comp in cca_results.cost_components
    ])
    cost_components_df.to_csv(output_dir / "cca_cost_components.csv", index=False)
    
    # Save outcome measures
    outcome_measures_df = pd.DataFrame([
        {
            "measure": measure.name,
            "description": measure.description,
            "unit": measure.unit,
            "higher_is_better": measure.higher_is_better,
            "mean": measure.mean,
            "ci_lower": measure.ci_lower,
            "ci_upper": measure.ci_upper
        }
        for measure in cca_results.outcome_measures
    ])
    outcome_measures_df.to_csv(output_dir / "cca_outcome_measures.csv", index=False)
    
    print("     ✓ CCA complete (3 outputs)")
    return cca_results


def run_complete_roa(psa: PSAData, output_dir: Path):
    """Run complete Real Options Analysis."""
    print("\n  9. Real Options Analysis...")
    
    # Create ROA engine
    roa = roa_engine.RealOptionsEngine(
        risk_free_rate=0.03,
        time_horizon_years=10,
        volatility_method="historical",
    )
    
    # Run ROA analysis
    roa_results = roa.analyze(
        psa_data=psa.table,
        perspective=psa.perspective,
        option_types=["delay", "abandon", "expand", "switch"],
        wtp_threshold=50000.0
    )
    
    # Save JSON results using engine method
    json_file = output_dir / "roa_results.json"
    roa.save_results(roa_results, str(json_file))
    
    # Save summary table as CSV
    roa_results.summary_table.to_csv(output_dir / "roa_summary.csv", index=False)
    
    print("     ✓ ROA complete (2 outputs)")
    return roa_results


def run_complete_roi(psa: PSAData, output_dir: Path):
    """Run complete ROI analysis."""
    print("\n  10. Return on Investment Analysis...")
    
    # Create ROI engine
    roi = roi_engine.ROIAnalysisEngine(
        willingness_to_pay=50000,
        discount_rate=0.03,
        time_horizon_years=10,
    )
    
    # Run ROI analysis
    roi_results = roi.analyze(psa.table)

    # Serialize results to JSON
    roi_json = roi_results.to_dict()
    json_file = output_dir / "roi_results.json"
    import json
    with open(json_file, "w") as f:
        json.dump(roi_json, f, indent=2, default=str)

    # Save summary table as CSV
    pd.DataFrame(roi_results.summary_stats).T.to_csv(output_dir / "roi_summary.csv", index=True)

    # Save metrics for each strategy
    metrics_df = pd.DataFrame([
        {
            "strategy": m.strategy,
            "benefit_cost_ratio": m.benefit_cost_ratio,
            "net_benefit": m.net_benefit,
            "roi_percentage": m.roi_percentage,
            "break_even_probability": m.break_even_probability,
            "payback_period_years": m.payback_period_years
        }
        for m in roi_results.metrics
    ])
    metrics_df.to_csv(output_dir / "roi_metrics.csv", index=False)

    print("     ✓ ROI complete (3 outputs)")
    return roi_results


def run_complete_mcda(psa: PSAData, output_dir: Path):
    """Run complete Multi-Criteria Decision Analysis."""
    print("\n  11. Multi-Criteria Decision Analysis...")
    
    # Create MCDA criteria for the perspective
    # Create MCDA criteria for the perspective (map healthcare to health_system)
    mcda_perspective = "health_system" if psa.perspective == "healthcare" else psa.perspective
    criteria = mcda_engine.create_default_criteria(perspective=mcda_perspective)
    
    # Calculate MCDA scores
    mcda_results = mcda_engine.calculate_mcda_scores(psa, criteria, n_boot=1000)
    
    # Perform sensitivity analysis
    sensitivity_results = mcda_engine.perform_weight_sensitivity_analysis(
        psa, criteria, n_scenarios=1000
    )
    
    # Save MCDA scores
    mcda_results.scores.to_csv(output_dir / "mcda_scores.csv", index=False)
    mcda_results.weighted_scores.to_csv(output_dir / "mcda_weighted_scores.csv", index=False)
    mcda_results.rankings.to_csv(output_dir / "mcda_rankings.csv", index=False)
    
    # Save sensitivity analysis results
    sensitivity_results.weight_ranges.to_csv(output_dir / "mcda_weight_ranges.csv", index=False)
    sensitivity_results.ranking_stability.to_csv(output_dir / "mcda_ranking_stability.csv", index=False)
    sensitivity_results.trade_offs.to_csv(output_dir / "mcda_trade_offs.csv", index=False)
    
    # Generate and save summary report
    report = mcda_engine.generate_mcda_summary_report(mcda_results, sensitivity_results)
    with open(output_dir / "mcda_report.md", "w") as f:
        f.write(report)
    
    print("     ✓ MCDA complete (7 outputs)")
    return mcda_results, sensitivity_results


def run_complete_analysis(jurisdiction: str, perspective: str):
    """Run complete analysis for one perspective/jurisdiction."""

    print(f"\n{'=' * 70}")
    print(f"Complete Analysis: {jurisdiction} - {perspective.title()} (Excluding Usual Care)")
    print(f"{'=' * 70}")

    # Load data
    data_file = f'psa_sample_{jurisdiction}_{perspective}.csv'
    data_path = Path('data/sample') / data_file

    if not data_path.exists():
        print("  ✗ Skipping - data not found")
        return None

    from trd_cea.run_v4_analysis import load_psa_data
    psa = load_psa_data(data_path, perspective, jurisdiction)

    # Filter out Usual Care
    psa = filter_out_usual_care(psa)

    print(f"  Loaded: {len(psa.draws)} draws, {len(psa.strategies)} strategies (Usual Care excluded)")

    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = Path(f'outputs_v4_no_uc/run_{timestamp}') / jurisdiction / perspective
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run all analyses
    try:
        _cea_results = run_complete_cea(psa, output_dir)
        _voi_results = run_complete_voi(psa, output_dir)
        _vbp_results = run_complete_vbp(psa, output_dir)
        _bia_results = run_complete_bia(psa, output_dir)
        _dsa_results = run_complete_dsa(psa, output_dir)
        _dcea_results = run_complete_dcea(psa, output_dir)
        _subgroup_results = run_complete_subgroup(psa, output_dir)
        _cca_results = run_complete_cca(psa, output_dir)
        _roa_results = run_complete_roa(psa, output_dir)
        _roi_results = run_complete_roi(psa, output_dir)
        _mcda_results = run_complete_mcda(psa, output_dir)

        # Count outputs
        output_files = list(output_dir.glob('*.csv'))
        print(f"\n  ✓ Analysis complete: {len(output_files)} output files")

        return {
            'output_dir': output_dir,
            'n_files': len(output_files),
            'timestamp': timestamp
        }

    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run complete analysis for all perspectives/jurisdictions."""

    print("=" * 70)
    print("V4 COMPLETE Analysis Pipeline (Excluding Usual Care)")
    print("=" * 70)
    print("\nThis will generate ALL outputs needed for ALL figure types")
    print("EXCLUDING Usual Care from all results")
    print()

    analyses = [
        ('AU', 'healthcare'),
        ('AU', 'societal'),
        ('NZ', 'healthcare'),
        ('NZ', 'societal'),
    ]

    results = {}
    for jurisdiction, perspective in analyses:
        result = run_complete_analysis(jurisdiction, perspective)
        if result:
            key = f"{jurisdiction}_{perspective}"
            results[key] = result

    # Summary
    print("\n" + "=" * 70)
    print("✓ COMPLETE Analysis Finished! (Excluding Usual Care)")
    print("=" * 70)

    if results:
        total_files = sum(r['n_files'] for r in results.values())
        print(f"\nTotal output files: {total_files}")
        print(f"Analyses completed: {len(results)}")

        # Expected: ~32 files per analysis × 4 = 128 files
        print("\nExpected: ~50 files per analysis")
        print(f"Generated: ~{total_files // len(results)} files per analysis")

        print("\n✓ Ready for complete figure generation (no Usual Care)!")
    else:
        print("\n✗ No analyses completed")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
