#!/usr/bin/env python3
"""
Command-line interface for Headroom Analysis.

This script provides a CLI for running headroom analysis on PSA data,
calculating maximum justifiable prices and development costs.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402
from analysis.core.io import load_psa, StrategyConfig  # noqa: E402
from analysis.engines.headroom_engine import HeadroomAnalysisEngine  # noqa: E402
from analysis.plotting.headroom_plots import HeadroomPlotter  # noqa: E402
from analysis.plotting.publication import validate_plot_completeness  # noqa: E402

# Set up logging
logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_wtp_thresholds(wtp_str: str) -> List[float]:
    """
    Parse WTP thresholds from string.

    Supports formats like:
    - "50000" (single value)
    - "30000,50000,70000" (comma-separated)
    - "30000:70000:5" (start:end:steps)

    Args:
        wtp_str: String representation of WTP thresholds

    Returns:
        List of WTP threshold values
    """
    if ':' in wtp_str:
        # Range format: start:end:steps
        parts = wtp_str.split(':')
        if len(parts) != 3:
            raise ValueError("Range format must be 'start:end:steps'")

        start = float(parts[0])
        end = float(parts[1])
        steps = int(parts[2])

        if steps < 2:
            raise ValueError("Steps must be at least 2")

        return list(np.linspace(start, end, steps))

    elif ',' in wtp_str:
        # Comma-separated format
        return [float(x.strip()) for x in wtp_str.split(',')]

    else:
        # Single value
        return [float(wtp_str)]


def load_config_file(config_path: Path) -> Dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        sys.exit(1)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Run Headroom Analysis for health economic evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic headroom analysis
  python scripts/run_headroom.py --psa data/psa.csv --strategies-config config/strategies.yml --wtp 50000 --output results/headroom/

  # Multiple WTP thresholds
  python scripts/run_headroom.py --psa data/psa.csv --strategies-config config/strategies.yml --wtp 30000,50000,70000 --output results/headroom/

  # WTP range
  python scripts/run_headroom.py --psa data/psa.csv --strategies-config config/strategies.yml --wtp 20000:80000:5 --output results/headroom/

  # With sensitivity analysis
  python scripts/run_headroom.py --psa data/psa.csv --strategies-config config/strategies.yml --wtp 50000 --sensitivity --output results/headroom/

  # Custom configuration
  python scripts/run_headroom.py --psa data/psa.csv --strategies-config config/strategies.yml --wtp 50000 --config config/headroom_config.yml --output results/headroom/
        """
    )

    # Required arguments
    parser.add_argument(
        '--psa', '-p',
        type=Path,
        required=True,
        help='Path to PSA data CSV file'
    )

    parser.add_argument(
        '--strategies-config', '-s',
        type=Path,
        required=True,
        help='Path to strategies configuration YAML file'
    )

    # WTP thresholds
    parser.add_argument(
        '--wtp', '-w',
        type=str,
        required=True,
        help='WTP thresholds: single value (50000), comma-separated (30000,50000,70000), or range (20000:80000:5)'
    )

    # Output options
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('results/headroom'),
        help='Output directory for results (default: results/headroom)'
    )

    # Optional configuration
    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Path to additional configuration YAML file'
    )

    # Analysis options
    parser.add_argument(
        '--strategies',
        type=str,
        nargs='+',
        help='Specific strategies to analyze (default: all in config)'
    )

    parser.add_argument(
        '--comparator',
        type=str,
        default='Usual care',
        help='Comparator strategy for headroom calculations (default: Usual care)'
    )

    parser.add_argument(
        '--sensitivity',
        action='store_true',
        help='Perform sensitivity analysis'
    )

    # Plotting options
    parser.add_argument(
        '--plots',
        action='store_true',
        default=True,
        help='Generate plots (default: True)'
    )

    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Generate interactive dashboard'
    )

    parser.add_argument(
        '--include-all-strategies',
        action='store_true',
        default=True,
        help='Include all 10 treatment strategies in plots even if they lack data (default: True)'
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

    args = parser.parse_args()

    # Setup logging
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        setup_logging(args.verbose)

    logger = logging.getLogger(__name__)

    try:
        # Validate inputs
        if not args.psa.exists():
            raise FileNotFoundError(f"PSA data file not found: {args.psa}")

        if not args.strategies_config.exists():
            raise FileNotFoundError(f"Strategies config file not found: {args.strategies_config}")

        # Parse WTP thresholds
        try:
            wtp_thresholds = parse_wtp_thresholds(args.wtp)
            logger.info(f"Using WTP thresholds: {wtp_thresholds}")
        except ValueError as e:
            logger.error(f"Invalid WTP threshold format: {e}")
            sys.exit(1)

        # Load configuration
        logger.info("Loading configuration files...")
        strategy_config = StrategyConfig.from_yaml(args.strategies_config)

        if args.config and args.config.exists():
            additional_config = load_config_file(args.config)
            logger.info(f"Loaded additional config from {args.config}")
        else:
            additional_config = {}

        # Load PSA data
        logger.info(f"Loading PSA data from {args.psa}")
        psa_data = load_psa(args.psa)

        # Filter strategies if specified
        if args.strategies:
            available_strategies = set(psa_data['strategy'].unique())
            requested_strategies = set(args.strategies)
            invalid_strategies = requested_strategies - available_strategies
            if invalid_strategies:
                logger.error(f"Requested strategies not found in PSA data: {invalid_strategies}")
                logger.info(f"Available strategies: {available_strategies}")
                sys.exit(1)
            strategies_to_analyze = list(requested_strategies)
        else:
            strategies_to_analyze = list(psa_data['strategy'].unique())

        # Remove comparator from strategies to analyze
        if args.comparator in strategies_to_analyze:
            strategies_to_analyze.remove(args.comparator)

        logger.info(f"Analyzing strategies: {strategies_to_analyze}")
        logger.info(f"Using comparator: {args.comparator}")

        # Create output directory
        args.output.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {args.output}")

        # Initialize engine and plotter
        engine = HeadroomAnalysisEngine()
        plotter = HeadroomPlotter()

        # Run main analysis
        logger.info("Running headroom analysis...")
        wtp_range = (min(wtp_thresholds), max(wtp_thresholds)) if len(wtp_thresholds) > 1 else (wtp_thresholds[0] * 0.5, wtp_thresholds[0] * 1.5)
        results = engine.analyze(
            psa_data=psa_data,
            wtp_range=wtp_range,
            current_prices=strategy_config.prices
        )

        # Save results
        results_file = args.output / "headroom_results.json"
        args.output.mkdir(parents=True, exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)
        logger.info(f"Results saved to {results_file}")

        # Save metrics as CSV
        metrics_df = pd.DataFrame([m.to_dict() for m in results.metrics])
        csv_file = args.output / "headroom_metrics.csv"
        metrics_df.to_csv(csv_file, index=False)
        logger.info(f"Metrics saved to {csv_file}")

        # Perform sensitivity analysis if requested
        if args.sensitivity:
            logger.info("Running sensitivity analysis...")
            # Note: Adjust method call based on actual API - removing undefined parameters
            sensitivity_results = engine.perform_sensitivity_analysis(
                psa_data=psa_data,
                parameter_ranges=additional_config.get('sensitivity_ranges', {
                    'wtp_variation': {'min': 0.8, 'max': 1.2, 'steps': 5},
                    'price_variation': {'min': 0.9, 'max': 1.1, 'steps': 3}
                })
            )

            sensitivity_file = args.output / "sensitivity_results.csv"
            sensitivity_results.to_csv(sensitivity_file, index=False)
            logger.info(f"Sensitivity results saved to {sensitivity_file}")

        # Generate plots
        if args.plots:
            logger.info("Generating plots...")

            # Load expected strategies from config
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            expected_strategies = list(config.keys())

            # Headroom curves
            fig_curves = plotter.plot_headroom_curves(
                results,
                save_path=args.output / "headroom_curves.png",
                include_all_strategies=args.include_all_strategies
            )
            validation = validate_plot_completeness(fig_curves, expected_strategies, "headroom curves")
            if not validation['complete']:
                logger.warning(f"Headroom curves plot incomplete: {validation['warnings']}")
            plt.close(fig_curves)

            # Threshold prices
            fig_thresholds = plotter.plot_threshold_prices(
                results,
                save_path=args.output / "threshold_prices.png",
                include_all_strategies=args.include_all_strategies
            )
            validation = validate_plot_completeness(fig_thresholds, expected_strategies, "threshold prices")
            if not validation['complete']:
                logger.warning(f"Threshold prices plot incomplete: {validation['warnings']}")
            plt.close(fig_thresholds)

            # Headroom distribution
            fig_distribution = plotter.plot_headroom_distribution(
                results,
                save_path=args.output / "headroom_distribution.png",
                include_all_strategies=args.include_all_strategies
            )
            validation = validate_plot_completeness(fig_distribution, expected_strategies, "headroom distribution")
            if not validation['complete']:
                logger.warning(f"Headroom distribution plot incomplete: {validation['warnings']}")
            plt.close(fig_distribution)

            # CE probabilities
            fig_ce = plotter.plot_cost_effectiveness_probabilities(
                results,
                save_path=args.output / "ce_probabilities.png",
                include_all_strategies=args.include_all_strategies
            )
            validation = validate_plot_completeness(fig_ce, expected_strategies, "CE probabilities")
            if not validation['complete']:
                logger.warning(f"CE probabilities plot incomplete: {validation['warnings']}")
            plt.close(fig_ce)

            logger.info(f"Plots saved to {args.output}")
            
            # Note: Plot validation completed above with validate_plot_completeness calls

        # Generate dashboard
        if args.dashboard:
            logger.info("Generating interactive dashboard...")
            dashboard_file = args.output / "headroom_dashboard.html"
            plotter.create_headroom_dashboard(
                results,
                save_path=dashboard_file
            )
            logger.info(f"Dashboard saved to {dashboard_file}")

        # Print summary
        if not args.quiet:
            print(f"\n{'='*60}")
            print("HEADROOM ANALYSIS COMPLETE")
            print(f"{'='*60}")
            print(f"Strategies analyzed: {len(strategies_to_analyze)}")
            print(f"WTP thresholds: {len(wtp_thresholds)}")
            print(f"Total metrics calculated: {len(results.metrics)}")
            print(f"Results saved to: {args.output}")
            print(f"{'='*60}")

            # Print top headroom opportunities
            print("\nTOP HEADROOM OPPORTUNITIES:")
            metrics_df = pd.DataFrame([m.to_dict() for m in results.metrics])
            for wtp in sorted(metrics_df['wtp_threshold'].unique(), reverse=True):
                wtp_data = metrics_df[metrics_df['wtp_threshold'] == wtp]
                top_strategy = wtp_data.loc[wtp_data['headroom_amount'].idxmax()]
                print(f"WTP ${wtp:,.0f}: {top_strategy['strategy']} "
                     f"(Headroom: ${top_strategy['headroom_amount']:,.0f}, "
                     f"Multiple: {top_strategy['headroom_multiple']:.1f}x)")

        logger.info("Headroom analysis completed successfully")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
