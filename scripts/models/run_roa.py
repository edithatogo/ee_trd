#!/usr/bin/env python3
"""
Real Options Analysis (ROA) CLI Tool for V4 Health Economic Evaluation

This script provides a command-line interface for running real options analysis
on health economic evaluation data.

Usage:
    python scripts/run_roa.py --psa-data data/psa.csv --perspective health_system --output results/roa_results.json

Author: V4 Development Team
Date: October 2025
"""

import argparse
import sys
from pathlib import Path
import logging
from typing import Optional

# Add analysis module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.engines.roa_engine import RealOptionsEngine, ROAResults  # noqa: E402
from analysis.plotting.roa_plots import ROAPlotter  # noqa: E402
from analysis.core.io import load_psa  # noqa: E402


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run Real Options Analysis for Health Economic Evaluation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic ROA analysis
  python scripts/run_roa.py --psa-data data/psa.csv --output results/roa.json

  # ROA with specific strategies and options
  python scripts/run_roa.py \\
    --psa-data data/psa.csv \\
    --strategies "IV-KA" "ECT" "rTMS" \\
    --option-types delay abandon expand \\
    --perspective health_system \\
    --output results/roa_custom.json \\
    --plots-dir figures/roa

  # ROA with custom parameters
  python scripts/run_roa.py \\
    --psa-data data/psa.csv \\
    --risk-free-rate 0.04 \\
    --time-horizon 7.0 \\
    --volatility 0.25 \\
    --output results/roa_custom_params.json
        """
    )

    # Required arguments
    parser.add_argument(
        '--psa-data',
        required=True,
        help='Path to PSA data file (CSV or JSON)'
    )

    parser.add_argument(
        '--output',
        required=True,
        help='Output path for ROA results (JSON format)'
    )

    # Optional analysis parameters
    parser.add_argument(
        '--strategies',
        nargs='+',
        help='List of strategies to analyze (default: all)'
    )

    parser.add_argument(
        '--perspective',
        choices=['health_system', 'societal'],
        default='health_system',
        help='Analysis perspective (default: health_system)'
    )

    parser.add_argument(
        '--option-types',
        nargs='+',
        choices=['delay', 'abandon', 'expand', 'switch'],
        default=['delay', 'abandon', 'expand'],
        help='Types of real options to value (default: delay abandon expand)'
    )

    # ROA model parameters
    parser.add_argument(
        '--risk-free-rate',
        type=float,
        default=0.03,
        help='Risk-free discount rate (default: 0.03)'
    )

    parser.add_argument(
        '--time-horizon',
        type=float,
        default=5.0,
        help='Time horizon for options in years (default: 5.0)'
    )

    parser.add_argument(
        '--volatility',
        type=float,
        help='Volatility assumption (default: estimated from data)'
    )

    # Plotting options
    parser.add_argument(
        '--plots-dir',
        help='Directory to save plots (creates multiple plot files)'
    )

    parser.add_argument(
        '--include-all-strategies',
        action='store_true',
        default=True,
        help='Include all 10 treatment strategies in plots even if they lack data (default: True)'
    )

    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Skip plot generation'
    )

    # Output options
    parser.add_argument(
        '--summary-table',
        help='Output path for summary table (CSV format)'
    )

    # Logging and debugging
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate inputs without running analysis'
    )

    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> bool:
    """Validate command line arguments."""
    # Check input file exists
    psa_path = Path(args.psa_data)
    if not psa_path.exists():
        logging.error(f"PSA data file not found: {psa_path}")
        return False

    # Check output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate numerical parameters
    if not (0 < args.risk_free_rate < 1):
        logging.error(f"Risk-free rate must be between 0 and 1: {args.risk_free_rate}")
        return False

    if args.time_horizon <= 0:
        logging.error(f"Time horizon must be positive: {args.time_horizon}")
        return False

    if args.volatility is not None and args.volatility <= 0:
        logging.error(f"Volatility must be positive: {args.volatility}")
        return False

    return True


def run_roa_analysis(args: argparse.Namespace) -> Optional[ROAResults]:
    """Run the ROA analysis."""
    try:
        logging.info("Starting Real Options Analysis...")

        # Initialize engine
        engine = RealOptionsEngine(
            risk_free_rate=args.risk_free_rate,
            time_horizon=args.time_horizon,
            volatility_assumption=args.volatility
        )

        # Load PSA data
        logging.info(f"Loading PSA data from {args.psa_data}")
        psa_data = load_psa(Path(args.psa_data))

        # Run analysis
        logging.info("Running ROA analysis...")
        results = engine.analyze(
            psa_data=psa_data,
            strategies=args.strategies,
            perspective=args.perspective,
            option_types=args.option_types
        )

        # Save results
        logging.info(f"Saving results to {args.output}")
        engine.save_results(results, args.output)

        # Save summary table if requested
        if args.summary_table:
            logging.info(f"Saving summary table to {args.summary_table}")
            results.summary_table.to_csv(args.summary_table, index=False)

        # Generate plots if requested
        if args.plots_dir and not args.no_plots:
            logging.info(f"Generating plots in {args.plots_dir}")
            plotter = ROAPlotter()
            plots_created = plotter.create_roa_report_plots(
                results,
                args.plots_dir,
                include_all_strategies=args.include_all_strategies
            )

            logging.info(f"Created {len(plots_created)} plots:")
            for plot_name, plot_path in plots_created.items():
                logging.info(f"  - {plot_name}: {plot_path}")
            
            # Validate plot completeness
            # Note: ROA plots are saved directly to files by create_roa_report_plots
            # Full validation would require loading saved matplotlib figures
            # For now, we rely on the include_all_strategies parameter ensuring completeness
            # and the individual plotting functions' placeholder logic

        logging.info("ROA analysis completed successfully!")
        return results

    except Exception as e:
        logging.error(f"ROA analysis failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return None


def print_summary(results: ROAResults) -> None:
    """Print analysis summary to console."""
    print("\n" + "="*60)
    print("REAL OPTIONS ANALYSIS SUMMARY")
    print("="*60)

    print(f"\nStrategies analyzed: {len(results.strategies)}")
    print(f"Options valued: {len(results.options)}")

    print("\nSTRATEGY RANKING (Total Value with Options):")
    print("-" * 50)

    # Sort strategies by total value
    sorted_strategies = sorted(
        results.total_value_with_options.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for i, (strategy, total_value) in enumerate(sorted_strategies, 1):
        _base_npv = results.risk_adjusted_npv[strategy]
        _flexibility = results.value_of_flexibility[strategy]
        print(f"{i}. {strategy}")
        print(".0f")
        print(".0f")
        print(".0f")
        print()

    print("OPTION VALUES BY TYPE:")
    print("-" * 30)

    # Aggregate option values by type
    option_totals = {}
    for strategy, options in results.option_values.items():
        for option_type, value in options.items():
            option_totals[option_type] = option_totals.get(option_type, 0) + value

    for option_type, total_value in option_totals.items():
        print(f"{option_type.capitalize():>12}: ${total_value:,.0f}")

    total_flexibility = sum(results.value_of_flexibility.values())
    print(f"\nTotal Value of Flexibility: ${total_flexibility:,.0f}")

    print("\n" + "="*60)


def main() -> int:
    """Main entry point."""
    args = parse_arguments()
    setup_logging(args.verbose)

    # Validate arguments
    if not validate_arguments(args):
        return 1

    # Dry run
    if args.dry_run:
        logging.info("Dry run completed - inputs validated successfully")
        return 0

    # Run analysis
    results = run_roa_analysis(args)

    if results is None:
        return 1

    # Print summary
    if not args.verbose:
        print_summary(results)

    return 0


if __name__ == '__main__':
    sys.exit(main())