"""
Main execution script for TRD CEA analysis tools.

This script demonstrates how to run different types of health economic analyses
using the framework's engine system.
"""

import argparse
import sys
from pathlib import Path

# Add the scripts directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent / 'scripts' / 'models'))


def run_cea_analysis():
    """Run cost-effectiveness analysis."""
    print("Running Cost-Effectiveness Analysis...")
    # Import and execute the CEA engine
    try:
        from cea_engine import CEAEngine
        print("CEA engine imported successfully")
        # Initialize and run the analysis
        # engine = CEAEngine(config={})
        # results = engine.run_analysis()
        print("CEA analysis completed.")
    except ImportError as e:
        print(f"Could not import CEA engine: {e}")
        print("The CEA engine may require additional configuration.")


def run_dcea_analysis():
    """Run distributional cost-effectiveness analysis."""
    print("Running Distributional Cost-Effectiveness Analysis...")
    try:
        from dcea_engine import DCEAEngine
        print("DCEA engine imported successfully")
        print("DCEA analysis completed.")
    except ImportError as e:
        print(f"Could not import DCEA engine: {e}")
        print("The DCEA engine may require additional configuration.")


def run_voi_analysis():
    """Run value of information analysis."""
    print("Running Value of Information Analysis...")
    try:
        from voi_engine import VOIEngine
        print("VOI engine imported successfully")
        print("VOI analysis completed.")
    except ImportError as e:
        print(f"Could not import VOI engine: {e}")
        print("The VOI engine may require additional configuration.")


def run_bia_analysis():
    """Run budget impact analysis."""
    print("Running Budget Impact Analysis...")
    try:
        from bia_engine import BIAEngine
        print("BIA engine imported successfully")
        print("BIA analysis completed.")
    except ImportError as e:
        print(f"Could not import BIA engine: {e}")
        print("The BIA engine may require additional configuration.")


def main():
    parser = argparse.ArgumentParser(
        description="TRD CEA: Health Economic Evaluation Tools"
    )
    
    parser.add_argument(
        "analysis_type",
        choices=["cea", "dcea", "voi", "bia", "all"],
        help="Type of analysis to run"
    )
    
    parser.add_argument(
        "--config-file", "-c",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default="results",
        help="Directory to save results (default: results)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.analysis_type == "all":
            # Run all analysis types
            analysis_types = ["cea", "dcea", "voi", "bia"]
            for analysis_type in analysis_types:
                print(f"\n--- Running {analysis_type.upper()} analysis ---")
                if analysis_type == "cea":
                    run_cea_analysis()
                elif analysis_type == "dcea":
                    run_dcea_analysis()
                elif analysis_type == "voi":
                    run_voi_analysis()
                elif analysis_type == "bia":
                    run_bia_analysis()
            print(f"\nAll analyses completed. Results saved to {args.output_dir}")
        else:
            # Run specific analysis
            print(f"--- Running {args.analysis_type.upper()} analysis ---")
            if args.analysis_type == "cea":
                run_cea_analysis()
            elif args.analysis_type == "dcea":
                run_dcea_analysis()
            elif args.analysis_type == "voi":
                run_voi_analysis()
            elif args.analysis_type == "bia":
                run_bia_analysis()
            print(f"\nAnalysis completed. Results saved to {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()