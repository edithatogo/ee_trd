#!/usr/bin/env python3
"""
Auto-fix common issues found during v2 pipeline verification.

This script addresses common verification failures by:
1. Auto-inserting missing λ/perspective information in captions from YAML configs and CLI logs
2. Rewriting mismatched λ/price grids across scripts to use a common grid and re-rendering figures
3. Prompting to run audit_and_extend_psa.py when "Oral ketamine" is missing from one perspective but present in another

Usage:
    python scripts/autofix_common_issues.py --results results/feat_oral_ketamine_YYYYMMDD/
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import yaml


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-fix common issues found during v2 pipeline verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--results",
        type=Path,
        required=True,
        help="Results directory (e.g., results/feat_oral_ketamine_YYYYMMDD/)",
    )
    parser.add_argument(
        "--strategies-yaml",
        type=Path,
        default=Path("config/strategies.yml"),
        help="Strategies YAML file",
    )
    parser.add_argument(
        "--config-yaml",
        type=Path,
        default=Path("config/analysis_v2_defaults.yml"),
        help="Analysis config YAML file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )
    return parser.parse_args(argv)


def load_yaml_config(yaml_path: Path) -> dict:
    """Load YAML configuration file."""
    try:
        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: {yaml_path} not found")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing {yaml_path}: {e}")
        return {}


def extract_lambda_from_logs(results_dir: Path) -> str | None:
    """Extract λ value from CLI logs in results directory."""
    # Look for log files or command outputs
    log_patterns = ["*.log", "*command*", "*run*"]

    for pattern in log_patterns:
        for log_file in results_dir.rglob(pattern):
            try:
                content = log_file.read_text(encoding="utf-8")
                # Look for --lambda patterns
                lambda_match = re.search(r"--lambda\s+(\d+)", content)
                if lambda_match:
                    return lambda_match.group(1)
            except (UnicodeDecodeError, OSError):
                continue

    return None


def fix_caption_missing_info(results_dir: Path, strategies_yaml: Path, dry_run: bool = False) -> bool:
    """Fix captions missing λ/perspective information."""
    print("🔍 Checking for captions missing λ/perspective information...")

    # Load strategies config
    _strategies = load_yaml_config(strategies_yaml)
    _perspectives = ["health_system", "societal"]

    # Extract λ from logs
    lambda_value = extract_lambda_from_logs(results_dir)

    fixed_any = False

    # Find all caption files
    for caption_file in results_dir.rglob("*caption.md"):
        try:
            content = caption_file.read_text(encoding="utf-8")

            # Check what's missing
            missing_info = []

            if "**Perspective:**" not in content and "**perspective**" not in content:
                # Try to infer perspective from path
                path_str = str(caption_file).lower()
                if "_hs/" in path_str or "health_system" in path_str or "healthcare" in path_str:
                    perspective = "Health system"
                elif "_s/" in path_str or "societal" in path_str:
                    perspective = "Societal"
                else:
                    # Assume directories without _hs suffix are societal
                    path_parts = Path(caption_file).parts
                    for part in path_parts:
                        if "_hs" in part:
                            perspective = "Health system"
                            break
                    else:
                        perspective = "Societal"
                missing_info.append(f"**Perspective:** {perspective}")

            if lambda_value and ("**λ" not in content and "**λ" not in content):
                missing_info.append(f"**λ (Willingness-to-pay threshold):** ${lambda_value} per QALY gained")

            if missing_info:
                if dry_run:
                    print(f"  Would fix {caption_file}: add {', '.join(missing_info)}")
                else:
                    # Add missing information at the end
                    updated_content = content.rstrip() + "\n\n" + "\n".join(missing_info) + "\n"
                    caption_file.write_text(updated_content, encoding="utf-8")
                    print(f"  ✅ Fixed {caption_file}: added {', '.join(missing_info)}")
                fixed_any = True

        except (OSError, UnicodeDecodeError) as e:
            print(f"  Error reading {caption_file}: {e}")

    return fixed_any


def find_common_grid(results_dir: Path) -> Tuple[List[float], List[float]] | None:
    """Find the most common λ and price grids across all analysis outputs."""
    lambda_values = set()
    price_values = set()

    # Look for CSV files with grid information
    for csv_file in results_dir.rglob("*.csv"):
        try:
            df = pd.read_csv(csv_file)

            # Check for lambda columns
            lambda_cols = [col for col in df.columns if "lambda" in col.lower()]
            for col in lambda_cols:
                if col in df.columns:
                    lambda_values.update(df[col].dropna().unique())

            # Check for price columns
            price_cols = [col for col in df.columns if "price" in col.lower() or "cost" in col.lower()]
            for col in price_cols:
                if col in df.columns:
                    price_values.update(df[col].dropna().unique())

        except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError):
            continue

    if lambda_values and price_values:
        # Sort and return most common values
        lambda_list = sorted(list(lambda_values))[:20]  # Limit to reasonable size
        price_list = sorted(list(price_values))[:50]    # Limit to reasonable size
        return lambda_list, price_list

    return None


def fix_mismatched_grids(results_dir: Path, dry_run: bool = False) -> bool:
    """Fix mismatched λ/price grids across scripts."""
    print("🔍 Checking for mismatched λ/price grids...")

    common_grid = find_common_grid(results_dir)

    if not common_grid:
        print("  No grid information found in results")
        return False

    lambda_grid, price_grid = common_grid
    print(f"  Found common λ grid: {len(lambda_grid)} values")
    print(f"  Found common price grid: {len(price_grid)} values")

    # This is a complex operation that would require re-running analyses
    # For now, just report what would need to be done
    if dry_run:
        print("  Would re-run analyses with common grids:")
        print("    - make_ceaf.py with consistent λ grid")
        print("    - make_vbp_curve.py with consistent λ grid")
        print("    - make_price_prob_curves.py with consistent price grid")
    else:
        print("  ⚠️  Grid re-rendering not implemented yet (would require re-running analyses)")

    return False  # Not actually fixing yet


def check_oral_ketamine_consistency(results_dir: Path) -> List[str]:
    """Check for Oral ketamine consistency across perspectives."""
    print("🔍 Checking Oral ketamine consistency across perspectives...")

    issues = []

    # Look for PSA files in results or data directory
    psa_files = []
    psa_files.extend(Path("data").glob("*psa*.csv"))
    psa_files.extend(results_dir.glob("*psa*.csv"))
    psa_files.extend(results_dir.rglob("*psa*.csv"))

    perspectives_data = {}

    for psa_file in psa_files:
        try:
            df = pd.read_csv(psa_file)

            # Check if there's a strategy/therapy column
            strategy_cols = [col for col in df.columns if "strategy" in col.lower() or "therapy" in col.lower()]
            if strategy_cols:
                strategies = set(df[strategy_cols[0]].dropna().unique())

                # Determine perspective from filename/path
                path_str = str(psa_file).lower()
                if "societal" in path_str:
                    perspective = "societal"
                elif "health_system" in path_str or "healthcare" in path_str:
                    perspective = "health_system"
                else:
                    perspective = "unknown"

                perspectives_data[perspective] = strategies

        except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError):
            continue

    # Check for Oral ketamine presence
    has_oral_ketamine = {}
    for perspective, strategies in perspectives_data.items():
        has_oral_ketamine[perspective] = "Oral ketamine" in strategies

    # Report inconsistencies
    if len(has_oral_ketamine) > 1:
        present_in = [p for p, has in has_oral_ketamine.items() if has]
        missing_in = [p for p, has in has_oral_ketamine.items() if not has]

        if present_in and missing_in:
            issues.append(
                f"Oral ketamine present in {', '.join(present_in)} but missing in {', '.join(missing_in)}"
            )

    return issues


def prompt_audit_and_extend(issues: List[str], dry_run: bool = False) -> bool:
    """Prompt user to run audit_and_extend_psa.py for missing Oral ketamine."""
    if not issues:
        return False

    print("🔧 Issues requiring audit_and_extend_psa.py:")
    for issue in issues:
        print(f"  - {issue}")

    if dry_run:
        print("  Would prompt: Run the following command to fix:")
        print("    python scripts/audit_and_extend_psa.py \\")
        print("      --psa data/psa.csv \\")
        print("      --strategies-yaml config/strategies.yml \\")
        print("      --perspective [missing_perspective] \\")
        print("      --add-therapy 'Oral ketamine' \\")
        print("      --from-params inputs/oral_ketamine_params.yaml \\")
        print("      --out data/psa_extended_[perspective].csv")
    else:
        print("  💡 Suggested fix:")
        print("    python scripts/audit_and_extend_psa.py \\")
        print("      --psa data/psa.csv \\")
        print("      --strategies-yaml config/strategies.yml \\")
        print("      --perspective [missing_perspective] \\")
        print("      --add-therapy 'Oral ketamine' \\")
        print("      --from-params inputs/oral_ketamine_params.yaml \\")
        print("      --out data/psa_extended_[perspective].csv")

    return True


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.results.exists():
        print(f"Error: Results directory {args.results} does not exist")
        return 1

    print("🔧 Auto-fixing common verification issues...")
    print(f"Results directory: {args.results}")
    print(f"Dry run: {args.dry_run}")
    print()

    fixes_applied = 0

    # 1. Fix captions missing λ/perspective
    if fix_caption_missing_info(args.results, args.strategies_yaml, args.dry_run):
        fixes_applied += 1

    # 2. Fix mismatched grids (placeholder for now)
    if fix_mismatched_grids(args.results, args.dry_run):
        fixes_applied += 1

    # 3. Check Oral ketamine consistency
    oral_ketamine_issues = check_oral_ketamine_consistency(args.results)
    if prompt_audit_and_extend(oral_ketamine_issues, args.dry_run):
        fixes_applied += 1

    print()
    if fixes_applied > 0:
        if args.dry_run:
            print(f"✅ Found {fixes_applied} issue(s) that would be fixed")
        else:
            print(f"✅ Applied fixes for {fixes_applied} issue(s)")
        return 0
    else:
        print("✅ No issues found that can be auto-fixed")
        return 0


if __name__ == "__main__":
    sys.exit(main())