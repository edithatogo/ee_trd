#!/usr/bin/env python3
"""
Command-line interface for Cost-Consequence Analysis (CCA)

This script provides a CLI for running cost-consequence analysis
on PSA data, generating disaggregated cost and outcome results.

Usage:
    python scripts/run_cca.py --psa-data data/psa.csv --perspective health_system

Author: V4 Development Team
Date: October 2025
"""

import argparse
import sys
from pathlib import Path

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis.engines.cca_engine import CostConsequenceEngine  # noqa: E402
from analysis.plotting.cca_plots import create_cca_report_plots  # noqa: E402
from analysis.core.io import load_psa  # noqa: E402


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Cost-Consequence Analysis (CCA)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic CCA analysis
    python scripts/run_cca.py --psa-data data/psa.csv --perspective health_system

    # CCA with specific strategies and output directory
    python scripts/run_cca.py --psa-data data/psa.csv --strategies "ECT" "IV-KA" --perspective health_system --output-dir results/cca_analysis

    # CCA with custom outcome measures
    python scripts/run_cca.py --psa-data data/psa.csv --outcome-measures effect remission_rate --perspective societal
        """
    )

    parser.add_argument(
        '--psa-data',
        type=str,
        required=True,
        help='Path to PSA data file (CSV or JSON)'
    )

    parser.add_argument(
        '--perspective',
        type=str,
        choices=['health_system', 'societal'],
        default='health_system',
        help='Analysis perspective (default: health_system)'
    )

    parser.add_argument(
        '--strategies',
        type=str,
        nargs='+',
        help='Specific strategies to analyze (default: all)'
    )

    parser.add_argument(
        '--outcome-measures',
        type=str,
        nargs='+',
        default=['effect'],
        help='Outcome measures to include (default: effect)'
    )

    parser.add_argument(
        '--cost-categories',
        type=str,
        nargs='+',
        help='Cost categories to break down (if available in data)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='results/cca_analysis',
        help='Output directory for results (default: results/cca_analysis)'
    )

    parser.add_argument(
        '--confidence-level',
        type=float,
        default=0.95,
        help='Confidence level for uncertainty intervals (default: 0.95)'
    )

    parser.add_argument(
        '--save-plots',
        action='store_true',
        help='Generate and save plots'
    )

    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducibility'
    )

    parser.add_argument(
        '--include-all-strategies',
        action='store_true',
        default=True,
        help='Include all 10 treatment strategies in plots even if they lack data (default: True)'
    )

    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if not Path(args.psa_data).exists():
        raise FileNotFoundError(f"PSA data file not found: {args.psa_data}")

    if not (0 < args.confidence_level < 1):
        raise ValueError("Confidence level must be between 0 and 1")

    if args.strategies:
        logger.info(f"Analyzing strategies: {', '.join(args.strategies)}")
    else:
        logger.info("Analyzing all available strategies")


def main() -> int:
    """Main CCA execution function."""
    try:
        args = parse_arguments()
        validate_arguments(args)

        logger.info("Starting Cost-Consequence Analysis (CCA)")
        logger.info(f"PSA data: {args.psa_data}")
        logger.info(f"Perspective: {args.perspective}")
        logger.info(f"Confidence level: {args.confidence_level}")

        # Initialize CCA engine
        engine = CostConsequenceEngine(
            confidence_level=args.confidence_level,
            random_seed=args.seed
        )

        # Load PSA data
        logger.info("Loading PSA data...")
        psa_data = load_psa(Path(args.psa_data))

        # Run CCA analysis
        logger.info("Running cost-consequence analysis...")
        results = engine.analyze(
            psa_data=psa_data,
            strategies=args.strategies,
            perspective=args.perspective,
            outcome_measures=args.outcome_measures,
            cost_categories=args.cost_categories
        )

        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save results
        results_path = output_dir / "cca_results.json"
        logger.info(f"Saving results to {results_path}")
        engine.save_results(results, str(results_path))

        # Display summary
        logger.info(f"CCA Analysis Summary: Strategies analyzed: {len(results.strategies)}, Cost components: {len(results.cost_components)}, Outcome measures: {len(results.outcome_measures)}")

        # Show summary table
        logger.info("Summary table generated")
        print("\n📊 Summary Table:")
        print(results.summary_table.to_string(index=False))

        # Generate plots if requested
        if args.save_plots:
            logger.info("Generating plots...")
            plot_paths = create_cca_report_plots(results, str(output_dir), include_all_strategies=args.include_all_strategies)
            logger.info(f"Generated {len(plot_paths)} plot files")

            for plot_name, plot_path in plot_paths.items():
                logger.info(f"Plot saved: {plot_name} -> {plot_path}")

            # Validate plot completeness
            _expected_strategies = [
                "ECT", "KA-ECT", "IV-KA", "IN-EKA", "PO-PSI", "PO-KA",
                "rTMS", "UC+Li", "UC+AA", "Usual care"
            ]

            if len(plot_paths) == 0:
                logger.warning("No plots were generated")
            else:
                logger.info(f"Generated {len(plot_paths)} plot files")

        logger.info(f"Results saved to: {output_dir}")
        logger.info("CCA analysis completed successfully")

        return 0

    except Exception as e:
        logger.error(f"CCA analysis failed: {e}", exc_info=True)
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
