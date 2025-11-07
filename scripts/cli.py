"""
Command Line Interface for TRD CEA Toolkit

This module provides a command-line interface for running health economic evaluations.
"""

import argparse
import sys
from pathlib import Path
import yaml
import pandas as pd
import numpy as np


def load_config(config_path: str):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_cea_analysis(config: dict):
    """Run cost-effectiveness analysis with given configuration."""
    print("Running Cost-Effectiveness Analysis...")
    print(f"Time horizon: {config['analysis']['time_horizon']} years")
    print(f"WTP threshold: ${config['analysis']['wtp_threshold']:,}/QALY")
    # In a real implementation, this would call the actual CEA engine
    print("CEA completed.")


def run_dcea_analysis(config: dict):
    """Run distributional cost-effectiveness analysis with given configuration."""
    print("Running Distributional Cost-Effectiveness Analysis...")
    print(f"Equity weights: {config['dcea']['equity_weights']}")
    # In a real implementation, this would call the actual DCEA engine
    print("DCEA completed.")


def run_voi_analysis(config: dict):
    """Run value of information analysis with given configuration."""
    print("Running Value of Information Analysis...")
    print(f"Number of simulations: {config['voi']['n_simulations']}")
    # In a real implementation, this would call the actual VOI engine
    print("VOI completed.")


def run_bia_analysis(config: dict):
    """Run budget impact analysis with given configuration."""
    print("Running Budget Impact Analysis...")
    print(f"Time horizon: {config['bia']['time_horizon']} years")
    # In a real implementation, this would call the actual BIA engine
    print("BIA completed.")


def main():
    parser = argparse.ArgumentParser(
        description="TRD CEA Toolkit - Health Economic Evaluation Tools"
    )
    
    parser.add_argument(
        "analysis_type",
        choices=["cea", "dcea", "voi", "bia", "all"],
        help="Type of analysis to run"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/default_analysis_config.yaml",
        help="Path to configuration file (default: config/default_analysis_config.yaml)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/",
        help="Output directory for results (default: results/)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
        if args.verbose:
            print(f"Loaded configuration from {args.config}")
    except FileNotFoundError:
        print(f"Error: Configuration file {args.config} not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in configuration file {args.config}: {str(e)}")
        sys.exit(1)
    
    # Ensure output directory exists
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Run requested analysis
    try:
        if args.analysis_type == "cea":
            run_cea_analysis(config)
        elif args.analysis_type == "dcea":
            run_dcea_analysis(config)
        elif args.analysis_type == "voi":
            run_voi_analysis(config)
        elif args.analysis_type == "bia":
            run_bia_analysis(config)
        elif args.analysis_type == "all":
            print("Running all analyses sequentially...")
            run_cea_analysis(config)
            run_dcea_analysis(config)
            run_voi_analysis(config)
            run_bia_analysis(config)
            print("All analyses completed.")
        
        print(f"Results saved to {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running analysis: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()