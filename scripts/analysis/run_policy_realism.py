#!/usr/bin/env python3
"""
Run Policy Realism Analysis for V4 Health Economic Evaluation

This script applies policy realism toggles to health economic analysis results,
providing country-specific and jurisdiction-specific policy configurations to
enable realistic implementation scenarios and sensitivity analysis.

Usage:
    python scripts/run_policy_realism.py --base-results data/psa.csv \
                                         --scenarios au_conservative au_progressive \
                                         --jurisdiction AU \
                                         --perspective health_system \
                                         --output-dir results/policy_analysis

Features:
- Apply multiple policy scenarios simultaneously
- Generate comprehensive sensitivity analysis
- Create publication-ready plots and reports
- Support for custom policy configurations

Author: V4 Development Team
Date: October 2025
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import json
from typing import Optional

from analysis.engines.policy_realism_engine import run_policy_analysis, PolicyRealismEngine
from analysis.plotting.policy_plots import create_policy_report_plots


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Policy Realism Analysis for V4 Health Economic Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic policy analysis for Australian conservative scenario
    python scripts/run_policy_realism.py --base-results data/psa.csv --scenarios au_conservative

    # Multiple scenarios with custom output directory
    python scripts/run_policy_realism.py --base-results results/cua_results.csv \\
                                         --scenarios au_conservative au_progressive nz_universal \\
                                         --jurisdiction AU --perspective health_system \\
                                         --output-dir results/policy_sensitivity

    # Use custom policy configuration
    python scripts/run_policy_realism.py --base-results data/psa.csv \\
                                         --scenarios custom_policy \\
                                         --config config/custom_policies.yaml

    # Generate plots only (skip analysis)
    python scripts/run_policy_realism.py --base-results results/policy_results/ \\
                                         --scenarios au_conservative \\
                                         --plots-only
        """
    )

    parser.add_argument(
        '--base-results',
        type=str,
        required=True,
        help='Path to base case analysis results CSV file'
    )

    parser.add_argument(
        '--scenarios',
        nargs='+',
        required=True,
        help='Policy scenario names to apply (space-separated)'
    )

    parser.add_argument(
        '--jurisdiction',
        type=str,
        default='AU',
        choices=['AU', 'NZ', 'both'],
        help='Jurisdiction for analysis (default: AU)'
    )

    parser.add_argument(
        '--perspective',
        type=str,
        default='health_system',
        choices=['health_system', 'societal'],
        help='Economic perspective (default: health_system)'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom policy configuration YAML file'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='results/policy_analysis',
        help='Output directory for results (default: results/policy_analysis)'
    )

    parser.add_argument(
        '--plots-only',
        action='store_true',
        help='Generate plots only (skip policy analysis)'
    )

    parser.add_argument(
        '--list-scenarios',
        action='store_true',
        help='List available policy scenarios and exit'
    )

    parser.add_argument(
        '--scenario-details',
        type=str,
        help='Show detailed configuration for a specific scenario'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    return parser.parse_args()


def validate_inputs(args):
    """Validate input arguments and files."""
    print("🔍 Validating inputs...")

    # Check base results file
    if not args.plots_only:
        base_results_path = Path(args.base_results)
        if not base_results_path.exists():
            print(f"❌ Base results file not found: {base_results_path}")
            return False

        # Check if it's a CSV file
        if base_results_path.suffix.lower() != '.csv':
            print(f"❌ Base results must be a CSV file: {base_results_path}")
            return False

        # Try to read the file to validate format
        try:
            df = pd.read_csv(base_results_path)
            required_cols = ['strategy', 'cost', 'effect']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"❌ Base results missing required columns: {missing_cols}")
                print(f"   Required columns: {required_cols}")
                return False
        except Exception as e:
            print(f"❌ Error reading base results file: {e}")
            return False

    # Check custom config file if provided
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ Custom config file not found: {config_path}")
            return False

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("✅ Input validation passed")
    return True


def list_available_scenarios(config_path: Optional[str] = None):
    """List all available policy scenarios."""
    engine = PolicyRealismEngine(config_path)

    print("\n📋 Available Policy Scenarios:")
    print("=" * 60)

    scenarios = engine.get_available_scenarios()

    for scenario_name in sorted(scenarios):
        scenario = engine.policy_scenarios[scenario_name]
        print(f"\n🔹 {scenario_name}")
        print(f"   Description: {scenario.description}")
        print(f"   Jurisdiction: {scenario.jurisdiction}")
        print(f"   Perspective: {scenario.perspective}")

        if scenario.reimbursement_rates:
            print(f"   Key reimbursement rates: {scenario.reimbursement_rates}")

    print(f"\n📊 Total scenarios available: {len(scenarios)}")


def show_scenario_details(scenario_name: str, config_path: Optional[str] = None):
    """Show detailed configuration for a specific scenario."""
    engine = PolicyRealismEngine(config_path)

    scenario = engine.get_scenario_details(scenario_name)
    if not scenario:
        print(f"❌ Scenario not found: {scenario_name}")
        return

    print(f"\n📋 Detailed Configuration for Scenario: {scenario_name}")
    print("=" * 60)
    print(f"Name: {scenario.name}")
    print(f"Description: {scenario.description}")
    print(f"Jurisdiction: {scenario.jurisdiction}")
    print(f"Perspective: {scenario.perspective}")

    print("\n💰 Reimbursement Rates:")
    for strategy, rate in scenario.reimbursement_rates.items():
        print(f"   {strategy}: {rate:.2%}")

    print("\n📋 Administrative Burden:")
    for strategy, burden in scenario.administrative_burden.items():
        print(f"   {strategy}: {burden:.1%}")

    print("\n🏥 Coverage Restrictions:")
    for strategy, restrictions in scenario.coverage_restrictions.items():
        print(f"   {strategy}: {restrictions}")

    print("\n📝 Prior Authorization Requirements:")
    for strategy, required in scenario.prior_authorization_requirements.items():
        print(f"   {strategy}: {'Yes' if required else 'No'}")

    if scenario.staffing_requirements:
        print("\n👥 Staffing Requirements:")
        for strategy, staff in scenario.staffing_requirements.items():
            print(f"   {strategy}: {staff}")

    if scenario.eligibility_criteria:
        print("\n✅ Eligibility Criteria:")
        for criterion, value in scenario.eligibility_criteria.items():
            print(f"   {criterion}: {value}")


def run_analysis(args):
    """Run the policy realism analysis."""
    print("🚀 Starting Policy Realism Analysis")
    print("=" * 50)

    # Set random seed for reproducibility
    import numpy as np
    np.random.seed(args.seed)

    # Run policy analysis
    print(f"📊 Applying {len(args.scenarios)} policy scenario(s)...")
    print(f"   Scenarios: {', '.join(args.scenarios)}")
    print(f"   Jurisdiction: {args.jurisdiction}")
    print(f"   Perspective: {args.perspective}")

    results = run_policy_analysis(
        base_results_path=args.base_results,
        scenario_names=args.scenarios,
        jurisdiction=args.jurisdiction,
        perspective=args.perspective,
        config_path=args.config,
        output_dir=args.output_dir
    )

    print("✅ Policy analysis completed successfully")

    # Generate summary report
    generate_summary_report(results, args.output_dir)

    return results


def generate_plots(results, output_dir: str):
    """Generate policy analysis plots."""
    print("📊 Generating policy analysis plots...")

    try:
        plot_files = create_policy_report_plots(results, f"{output_dir}/figures")
        print(f"✅ Created {len(plot_files)} plots in {output_dir}/figures")

        # List created plots
        for plot_name, file_path in plot_files.items():
            print(f"   📈 {plot_name}: {file_path}")

    except Exception as e:
        print(f"⚠️  Error generating plots: {e}")


def generate_summary_report(results, output_dir: str):
    """Generate a summary report of the policy analysis."""
    print("📝 Generating summary report...")

    summary_path = Path(output_dir) / "policy_analysis_summary.json"

    # Create comprehensive summary
    summary = {
        "analysis_info": {
            "total_scenarios_applied": len(results.policy_scenario_results),
            "scenarios": list(results.policy_scenario_results.keys()),
            "jurisdiction": results.policy_summary.get('jurisdiction'),
            "perspective": results.policy_summary.get('perspective'),
            "base_case_strategies": len(results.base_case_results['strategy'].unique()),
            "total_draws": len(results.base_case_results)
        },
        "policy_summary": results.policy_summary,
        "sensitivity_analysis_summary": {
            "total_comparisons": len(results.sensitivity_analysis),
            "strategies_analyzed": results.sensitivity_analysis['strategy'].nunique(),
            "scenarios_analyzed": results.sensitivity_analysis['scenario'].nunique(),
            "avg_cost_change_percent": results.sensitivity_analysis['cost_change_percent'].mean(),
            "max_cost_change_percent": results.sensitivity_analysis['cost_change_percent'].max(),
            "min_cost_change_percent": results.sensitivity_analysis['cost_change_percent'].min()
        },
        "implementation_impact_summary": {
            "total_impacts_calculated": len(results.implementation_impact),
            "strategies_impacted": results.implementation_impact['strategy'].nunique(),
            "avg_cost_impact_percent": results.implementation_impact['cost_impact_percent'].mean(),
            "complexity_distribution": results.implementation_impact['implementation_complexity'].value_counts().to_dict()
        },
        "key_findings": results.policy_summary.get('key_findings', [])
    }

    # Save summary
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"✅ Summary report saved to {summary_path}")

    # Print key findings to console
    print("\n🔑 Key Findings:")
    for finding in summary['key_findings']:
        print(f"   • {finding}")

    print("\n📊 Analysis Summary:")
    print(f"   • Scenarios applied: {summary['analysis_info']['total_scenarios_applied']}")
    print(f"   • Strategies analyzed: {summary['analysis_info']['base_case_strategies']}")
    print(f"   • Total draws: {summary['analysis_info']['total_draws']}")
    print(f"   • Average cost change: {summary['sensitivity_analysis_summary']['avg_cost_change_percent']:.2f}%")
    print(f"   • Maximum cost change: {summary['sensitivity_analysis_summary']['max_cost_change_percent']:.2f}%")
def main():
    """Main execution function."""
    args = parse_arguments()

    # Handle special modes
    if args.list_scenarios:
        list_available_scenarios(args.config)
        return 0

    if args.scenario_details:
        show_scenario_details(args.scenario_details, args.config)
        return 0

    # Validate inputs
    if not validate_inputs(args):
        return 1

    try:
        if args.plots_only:
            # Load existing results for plotting only
            print("🎨 Generating plots from existing results...")

            # This would need to be implemented to load existing PolicyToggleResults
            # For now, we'll skip this functionality
            print("⚠️  Plots-only mode not yet implemented")
            return 1

        else:
            # Run full analysis
            results = run_analysis(args)

            # Generate plots
            generate_plots(results, args.output_dir)

        print("\n🎉 Policy realism analysis completed successfully!")
        print(f"   📁 Results saved to: {args.output_dir}")

        return 0

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())