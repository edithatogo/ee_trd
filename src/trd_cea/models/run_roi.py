#!/usr/bin/env python3
"""
Command-line interface for Return on Investment (ROI) Analysis.

This script provides a CLI tool for running comprehensive ROI analysis
on health economic evaluation data, including benefit-cost ratios,
payback period calculations, and sensitivity analysis.
"""

import argparse
import sys
from pathlib import Path
import logging

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from trd_cea.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

# Add analysis module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from trd_cea.core.io import load_psa  # noqa: E402
from analysis.engines.roi_engine import ROIAnalysisEngine  # noqa: E402
from analysis.plotting.roi_plots import ROIPlotter  # noqa: E402
from analysis.plotting.publication import validate_plot_completeness  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Return on Investment (ROI) Analysis for Health Economic Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic ROI analysis
  python scripts/run_roi.py --psa-data data/psa.csv --output results/roi_results.json

  # ROI analysis with custom parameters
  python scripts/run_roi.py --psa-data data/psa.csv --wtp 75000 --discount-rate 0.03 --time-horizon 10 --output results/roi_custom.json

  # ROI analysis for specific strategies
  python scripts/run_roi.py --psa-data data/psa.csv --strategies "IV-KA" "ECT" --output results/roi_selected.json

  # ROI analysis with plots
  python scripts/run_roi.py --psa-data data/psa.csv --output results/roi_results.json --plot-dir figures/roi/

  # Sensitivity analysis
  python scripts/run_roi.py --psa-data data/psa.csv --sensitivity --param-ranges config/sensitivity_ranges.yml --output results/roi_sensitivity.csv
        """
    )

    # Required arguments
    parser.add_argument(
        '--psa-data',
        type=str,
        required=True,
        help='Path to PSA data CSV file'
    )

    # Optional analysis parameters
    parser.add_argument(
        '--wtp',
        type=float,
        default=50000,
        help='Willingness to pay threshold (default: 50000)'
    )

    parser.add_argument(
        '--discount-rate',
        type=float,
        default=0.05,
        help='Annual discount rate (default: 0.05)'
    )

    parser.add_argument(
        '--time-horizon',
        type=int,
        default=5,
        help='Analysis time horizon in years (default: 5)'
    )

    # Strategy selection
    parser.add_argument(
        '--strategies',
        nargs='+',
        help='Specific strategies to analyze (default: all)'
    )

    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save ROI results JSON file'
    )

    parser.add_argument(
        '--plot-dir',
        type=str,
        help='Directory to save ROI plots (creates multiple plot files)'
    )

    parser.add_argument(
        '--include-all-strategies',
        action='store_true',
        default=True,
        help='Include all 10 treatment strategies in plots even if they lack data (default: True)'
    )

    # Sensitivity analysis
    parser.add_argument(
        '--sensitivity',
        action='store_true',
        help='Perform sensitivity analysis'
    )

    parser.add_argument(
        '--param-ranges',
        type=str,
        help='YAML file with parameter ranges for sensitivity analysis'
    )

    parser.add_argument(
        '--n-samples',
        type=int,
        default=1000,
        help='Number of samples for sensitivity analysis (default: 1000)'
    )

    parser.add_argument(
        '--sensitivity-output',
        type=str,
        help='Path to save sensitivity analysis results CSV'
    )

    # Logging options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )

    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command-line arguments."""
    # Check PSA data file exists
    psa_path = Path(args.psa_data)
    if not psa_path.exists():
        raise FileNotFoundError(f"PSA data file not found: {psa_path}")

    # Validate parameter ranges
    if args.discount_rate < 0 or args.discount_rate > 1:
        raise ValueError("Discount rate must be between 0 and 1")

    if args.time_horizon <= 0:
        raise ValueError("Time horizon must be positive")

    if args.wtp <= 0:
        raise ValueError("WTP must be positive")

    # Check sensitivity analysis requirements
    if args.sensitivity:
        if not args.param_ranges:
            raise ValueError("--param-ranges required for sensitivity analysis")
        if not Path(args.param_ranges).exists():
            raise FileNotFoundError(f"Parameter ranges file not found: {args.param_ranges}")

    # Create output directories if needed
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.plot_dir:
        plot_dir = Path(args.plot_dir)
        plot_dir.mkdir(parents=True, exist_ok=True)

    if args.sensitivity_output:
        sens_path = Path(args.sensitivity_output)
        sens_path.parent.mkdir(parents=True, exist_ok=True)


def load_parameter_ranges(ranges_file: str) -> dict:
    """Load parameter ranges from YAML file."""
    try:
        import yaml
        with open(ranges_file, 'r') as f:
            ranges = yaml.safe_load(f)
        return ranges
    except ImportError:
        raise ImportError("PyYAML required for sensitivity analysis. Install with: pip install PyYAML")
    except Exception as e:
        raise ValueError(f"Error loading parameter ranges: {e}")


def run_roi_analysis(args: argparse.Namespace) -> dict:
    """Run the main ROI analysis."""
    logger.info("Starting ROI analysis")

    # Load PSA data
    logger.info(f"Loading PSA data from {args.psa_data}")
    psa_data = load_psa(Path(args.psa_data))

    # Initialize ROI engine
    engine = ROIAnalysisEngine(
        willingness_to_pay=args.wtp,
        discount_rate=args.discount_rate,
        time_horizon_years=args.time_horizon,
    )

    # Run analysis
    results = engine.analyze(
        psa_data=psa_data,
        strategies=args.strategies,
        save_path=Path(args.output) if args.output else None,
    )

    logger.info("ROI analysis completed")
    return results.to_dict()


def generate_plots(roi_results: dict, plot_dir: Path, include_all_strategies: bool = True) -> dict:
    """Generate and save ROI plots."""
    logger.info(f"Generating plots in {plot_dir}")

    # Load expected strategies from config
    from trd_cea.core.io import load_strategies_config
    config = load_strategies_config()
    expected_strategies = list(config.keys())

    plotter = ROIPlotter()
    plot_paths = {}

    # Create individual plots
    fig_bcr = plotter.plot_benefit_cost_ratios(
        roi_results,
        save_path=plot_dir / "benefit_cost_ratios.png",
        include_all_strategies=include_all_strategies
    )
    validation = validate_plot_completeness(fig_bcr, expected_strategies, "benefit-cost ratios")
    if not validation['complete']:
        logger.warning(f"Benefit-cost ratios plot incomplete: {validation['warnings']}")
    plt.close(fig_bcr)
    plot_paths['benefit_cost_ratios'] = plot_dir / "benefit_cost_ratios.png"

    fig_roi = plotter.plot_roi_percentages(
        roi_results,
        save_path=plot_dir / "roi_percentages.png",
        include_all_strategies=include_all_strategies
    )
    validation = validate_plot_completeness(fig_roi, expected_strategies, "ROI percentages")
    if not validation['complete']:
        logger.warning(f"ROI percentages plot incomplete: {validation['warnings']}")
    plt.close(fig_roi)
    plot_paths['roi_percentages'] = plot_dir / "roi_percentages.png"

    fig_payback = plotter.plot_payback_periods(
        roi_results,
        save_path=plot_dir / "payback_periods.png",
        include_all_strategies=include_all_strategies
    )
    validation = validate_plot_completeness(fig_payback, expected_strategies, "payback periods")
    if not validation['complete']:
        logger.warning(f"Payback periods plot incomplete: {validation['warnings']}")
    plt.close(fig_payback)
    plot_paths['payback_periods'] = plot_dir / "payback_periods.png"

    fig_be = plotter.plot_break_even_probabilities(
        roi_results,
        save_path=plot_dir / "break_even_probabilities.png",
        include_all_strategies=include_all_strategies
    )
    validation = validate_plot_completeness(fig_be, expected_strategies, "break-even probabilities")
    if not validation['complete']:
        logger.warning(f"Break-even probabilities plot incomplete: {validation['warnings']}")
    plt.close(fig_be)
    plot_paths['break_even_probabilities'] = plot_dir / "break_even_probabilities.png"

    fig_stats = plotter.plot_roi_summary_stats(
        roi_results,
        save_path=plot_dir / "roi_summary_stats.png"
    )
    # Summary stats plot doesn't include strategies, so skip validation
    plt.close(fig_stats)
    plot_paths['roi_summary_stats'] = plot_dir / "roi_summary_stats.png"

    # Create interactive dashboard
    plot_paths['roi_dashboard'] = plotter.create_roi_dashboard(
        roi_results,
        save_path=plot_dir / "roi_dashboard.html"
    )

    logger.info("Plot generation completed")
    return plot_paths


def run_sensitivity_analysis(args: argparse.Namespace, psa_data: pd.DataFrame) -> pd.DataFrame:
    """Run sensitivity analysis."""
    logger.info("Running sensitivity analysis")

    # Load parameter ranges
    param_ranges = load_parameter_ranges(args.param_ranges)

    # Initialize engine
    engine = ROIAnalysisEngine(
        willingness_to_pay=args.wtp,
        discount_rate=args.discount_rate,
        time_horizon_years=args.time_horizon,
    )

    # Run sensitivity analysis
    sensitivity_results = engine.perform_sensitivity_analysis(
        psa_data=psa_data,
        parameter_ranges=param_ranges,
        n_samples=args.n_samples,
    )

    # Save results if requested
    if args.sensitivity_output:
        sensitivity_results.to_csv(args.sensitivity_output, index=False)
        logger.info(f"Sensitivity results saved to {args.sensitivity_output}")

    return sensitivity_results


def print_summary(roi_results: dict) -> None:
    """Print analysis summary to console."""
    print("\n" + "="*60)
    print("RETURN ON INVESTMENT (ROI) ANALYSIS SUMMARY")
    print("="*60)

    metadata = roi_results["analysis_metadata"]
    print(f"Willingness to Pay: ${metadata['willingness_to_pay']:,.0f}")
    print(f"Discount Rate: {metadata['discount_rate']:.1%}")
    print(f"Time Horizon: {metadata['time_horizon_years']} years")
    print(f"Number of Strategies: {metadata['n_strategies']}")
    print(f"Number of PSA Draws: {metadata['n_psa_draws']}")

    print("\nSTRATEGY-SPECIFIC RESULTS:")
    print("-" * 40)

    for metric in roi_results["metrics"]:
        print(f"\nStrategy: {metric['strategy']}")
        print(".2f")
        print(".2f")
        print(".1f")
        print(".1%")
        if metric['payback_period_years'] is not None:
            print(".1f")
        else:
            print("  Payback Period: N/A")

    print("\nSUMMARY STATISTICS:")
    print("-" * 40)

    summary_stats = roi_results["summary_stats"]
    for metric_name, stats in summary_stats.items():
        formatted_name = metric_name.replace('_', ' ').title()
        print(f"\n{formatted_name}:")
        print(".2f")
        print(".2f")
        print(".2f")
        print(".2f")

    print("\n" + "="*60)


def main() -> int:
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Configure logging
        if args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
        elif args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Validate arguments
        validate_arguments(args)

        # Run main analysis
        roi_results = run_roi_analysis(args)

        # Generate plots if requested
        if args.plot_dir:
            plot_paths = generate_plots(roi_results, Path(args.plot_dir), include_all_strategies=args.include_all_strategies)
            
            # Validate plot completeness
            _expected_strategies = [
                "ECT", "KA-ECT", "IV-KA", "IN-EKA", "PO-PSI", "PO-KA", 
                "rTMS", "UC+Li", "UC+AA", "Usual care"
            ]
            
            if len(plot_paths) == 0:
                logger.warning("No plots were generated")
            else:
                logger.info(f"Generated {len(plot_paths)} plot files")
                # Note: Full plot validation would require loading saved figures
                # For now, we rely on the include_all_strategies parameter ensuring completeness

        # Run sensitivity analysis if requested
        if args.sensitivity:
            psa_data = load_psa(Path(args.psa_data))
            sensitivity_results = run_sensitivity_analysis(args, psa_data)
            logger.info(f"Sensitivity analysis completed with {len(sensitivity_results)} scenarios")

        # Print summary
        if not args.quiet:
            print_summary(roi_results)

        logger.info("ROI analysis pipeline completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Error during ROI analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
