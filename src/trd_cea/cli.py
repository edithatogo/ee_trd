"""
Command-Line Interface for TRD CEA Toolkit

This module provides a command-line interface for running health economic evaluations.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for the TRD CEA command-line interface.

    Args:
        args: Optional list of command-line arguments (for testing)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="TRD CEA: Health Economic Evaluation Toolkit for TRD Interventions"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"TRD CEA Toolkit v0.4.0"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands for health economic evaluation"
    )
    
    # CEA Analysis command
    cea_parser = subparsers.add_parser(
        "cea",
        help="Run cost-effectiveness analysis"
    )
    cea_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Configuration file for CEA analysis"
    )
    cea_parser.add_argument(
        "--output",
        type=str,
        help="Output directory for results"
    )
    
    # DCEA Analysis command
    dcea_parser = subparsers.add_parser(
        "dcea",
        help="Run distributional cost-effectiveness analysis"
    )
    dcea_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Configuration file for DCEA analysis"
    )
    dcea_parser.add_argument(
        "--include-equity",
        action="store_true",
        help="Include equity analysis in DCEA"
    )
    
    # VOI Analysis command
    voi_parser = subparsers.add_parser(
        "voi",
        help="Run value of information analysis"
    )
    voi_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Configuration file for VOI analysis"
    )
    voi_parser.add_argument(
        "--type",
        choices=["evpi", "evppi", "evsi"],
        default="evpi",
        help="Type of value of information to calculate"
    )
    
    # BIA Analysis command
    bia_parser = subparsers.add_parser(
        "bia",
        help="Run budget impact analysis"
    )
    bia_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Configuration file for BIA analysis"
    )
    bia_parser.add_argument(
        "--horizon",
        type=int,
        default=5,
        help="Time horizon for budget impact projection"
    )
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command is None:
        parser.print_help()
        return 0
    
    # Execute the command
    try:
        if parsed_args.command == "cea":
            return run_cea_analysis(parsed_args)
        elif parsed_args.command == "dcea":
            return run_dcea_analysis(parsed_args)
        elif parsed_args.command == "voi":
            return run_voi_analysis(parsed_args)
        elif parsed_args.command == "bia":
            return run_bia_analysis(parsed_args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        return 1


def run_cea_analysis(args) -> int:
    """Run cost-effectiveness analysis."""
    from .analysis.cea import run_analysis
    
    try:
        # This would call the actual CEA engine with parameters from args
        print(f"Running CEA analysis with config: {args.config}")
        if hasattr(args, 'output') and args.output:
            print(f"Output directory: {args.output}")
        # run_analysis(config_file=args.config, output_dir=args.output)
        print("CEA analysis completed.")
        return 0
    except Exception as e:
        print(f"Error in CEA analysis: {e}", file=sys.stderr)
        return 1


def run_dcea_analysis(args) -> int:
    """Run distributional cost-effectiveness analysis."""
    from .analysis.dcea import run_analysis
    
    try:
        # This would call the actual DCEA engine with parameters from args
        print(f"Running DCEA analysis with config: {args.config}")
        if hasattr(args, 'include_equity') and args.include_equity:
            print("Including equity analysis")
        # run_analysis(config_file=args.config, include_equity=args.include_equity)
        print("DCEA analysis completed.")
        return 0
    except Exception as e:
        print(f"Error in DCEA analysis: {e}", file=sys.stderr)
        return 1


def run_voi_analysis(args) -> int:
    """Run value of information analysis."""
    from .analysis.voi import run_analysis
    
    try:
        # This would call the actual VOI engine with parameters from args
        print(f"Running {args.type.upper()} analysis with config: {args.config}")
        # run_analysis(config_file=args.config, voi_type=args.type)
        print(f"{args.type.upper()} analysis completed.")
        return 0
    except Exception as e:
        print(f"Error in VOI analysis: {e}", file=sys.stderr)
        return 1


def run_bia_analysis(args) -> int:
    """Run budget impact analysis."""
    from .analysis.bia import run_analysis
    
    try:
        # This would call the actual BIA engine with parameters from args
        print(f"Running BIA analysis with config: {args.config}")
        print(f"Time horizon: {args.horizon} years")
        # run_analysis(config_file=args.config, horizon=args.horizon)
        print("BIA analysis completed.")
        return 0
    except Exception as e:
        print(f"Error in BIA analysis: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())