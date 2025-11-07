#!/usr/bin/env python3
"""Reconcile v1 vs v2 analysis outputs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd


def find_csv_files(root: Path) -> dict[str, Path]:
    """Find all CSV files recursively, keyed by filename."""
    csv_files = {}
    for csv_file in root.rglob("*.csv"):
        csv_files[csv_file.name] = csv_file
    return csv_files


def find_figure_files(root: Path) -> dict[str, Path]:
    """Find all figure files (png, pdf, svg) recursively."""
    figures = {}
    for ext in ["png", "pdf", "svg"]:
        for fig_file in root.rglob(f"*.{ext}"):
            figures[fig_file.name] = fig_file
    return figures


def compare_csvs(v1_path: Path, v2_path: Path, tol: float) -> dict:
    """Compare two CSV files and return diff metrics."""
    try:
        df1 = pd.read_csv(v1_path)
        df2 = pd.read_csv(v2_path)
    except Exception as e:
        return {"error": str(e)}

    # Find common columns
    common_cols = set(df1.columns) & set(df2.columns)
    if not common_cols:
        return {"error": "No common columns"}

    # Align on common columns
    df1_common = df1[list(common_cols)]
    df2_common = df2[list(common_cols)]

    # Sort deterministically - try to find a good sort key
    sort_cols = []
    for col in common_cols:
        if col in ["draw", "strategy", "perspective", "lambda", "price"]:
            sort_cols.append(col)
    if sort_cols:
        df1_common = df1_common.sort_values(sort_cols).reset_index(drop=True)
        df2_common = df2_common.sort_values(sort_cols).reset_index(drop=True)

    # Check if shapes match
    shape_match = df1_common.shape == df2_common.shape

    # Compute differences
    diff_df = df1_common.copy()
    max_abs_diffs = {}
    changed_rows = 0

    for col in common_cols:
        if pd.api.types.is_numeric_dtype(df1_common[col]) and not pd.api.types.is_bool_dtype(df1_common[col]):
            diff = (df1_common[col] - df2_common[col]).abs()
            max_abs_diffs[col] = diff.max()
            diff_df[f"{col}_diff"] = diff
            changed_rows += (diff > tol).sum()
        else:
            # For non-numeric or boolean, check equality
            diff_df[f"{col}_match"] = df1_common[col] == df2_common[col]
            changed_rows += (~(df1_common[col] == df2_common[col])).sum()

    total_rows = len(df1_common)
    changed_pct = (changed_rows / total_rows * 100) if total_rows > 0 else 0

    # Added/removed rows (if shapes differ)
    added_rows = (
        len(df2_common) - len(df1_common) if len(df2_common) > len(df1_common) else 0
    )
    removed_rows = (
        len(df1_common) - len(df2_common) if len(df1_common) > len(df2_common) else 0
    )

    return {
        "shape_match": shape_match,
        "total_rows": total_rows,
        "changed_rows": changed_rows,
        "changed_pct": changed_pct,
        "max_abs_diffs": max_abs_diffs,
        "added_rows": added_rows,
        "removed_rows": removed_rows,
        "diff_df": diff_df,
    }


def compare_figures(
    v1_figures: dict[str, Path], v2_figures: dict[str, Path]
) -> dict[str, dict]:
    """Compare figure files presence and sizes."""
    all_fig_names = set(v1_figures.keys()) | set(v2_figures.keys())
    comparisons = {}

    for fig_name in all_fig_names:
        comp = {
            "v1_exists": fig_name in v1_figures,
            "v2_exists": fig_name in v2_figures,
        }

        if comp["v1_exists"]:
            comp["v1_size"] = v1_figures[fig_name].stat().st_size
        if comp["v2_exists"]:
            comp["v2_size"] = v2_figures[fig_name].stat().st_size

        if comp["v1_exists"] and comp["v2_exists"]:
            comp["size_diff"] = abs(comp["v1_size"] - comp["v2_size"])
        elif comp["v1_exists"] and not comp["v2_exists"]:
            comp["warning"] = "v1 figure missing in v2"

        comparisons[fig_name] = comp

    return comparisons


def write_csv_diff(outdir: Path, filename: str, diff_data: dict) -> None:
    """Write CSV diff to file."""
    if "diff_df" in diff_data:
        diff_data["diff_df"].to_csv(outdir / f"{filename}_diff.csv", index=False)


def write_summary(
    outdir: Path, csv_comparisons: dict, figure_comparisons: dict, tol: float
) -> None:
    """Write consolidated summary.md."""
    outdir.mkdir(parents=True, exist_ok=True)
    summary_path = outdir / "summary.md"

    with open(summary_path, "w") as f:
        f.write("# V1 vs V2 Reconciliation Report\n\n")
        f.write(f"Tolerance: {tol}\n\n")

        f.write("## CSV Comparisons\n\n")
        all_within_tol = True

        for filename, comp in csv_comparisons.items():
            f.write(f"### {filename}\n\n")
            if "error" in comp:
                f.write(f"Error: {comp['error']}\n\n")
                all_within_tol = False
                continue

            f.write(f"- Shape match: {comp['shape_match']}\n")
            f.write(f"- Total rows: {comp['total_rows']}\n")
            f.write(
                f"- Changed rows: {comp['changed_rows']} ({comp['changed_pct']:.2f}%)\n"
            )
            f.write(f"- Added rows: {comp['added_rows']}\n")
            f.write(f"- Removed rows: {comp['removed_rows']}\n")

            if comp["max_abs_diffs"]:
                f.write("- Max absolute differences:\n")
                for col, max_diff in comp["max_abs_diffs"].items():
                    f.write(f"  - {col}: {max_diff}\n")
                    if max_diff > tol:
                        all_within_tol = False

            f.write("\n")

        f.write("## Figure Comparisons\n\n")
        for fig_name, comp in figure_comparisons.items():
            f.write(f"### {fig_name}\n\n")
            f.write(f"- V1 exists: {comp['v1_exists']}\n")
            f.write(f"- V2 exists: {comp['v2_exists']}\n")

            if "v1_size" in comp:
                f.write(f"- V1 size: {comp['v1_size']} bytes\n")
            if "v2_size" in comp:
                f.write(f"- V2 size: {comp['v2_size']} bytes\n")
            if "size_diff" in comp:
                f.write(f"- Size difference: {comp['size_diff']} bytes\n")
            if "warning" in comp:
                f.write(f"- **Warning:** {comp['warning']}\n")
                all_within_tol = False

            f.write("\n")

        f.write("## Summary\n\n")
        status = "PASS" if all_within_tol else "FAIL"
        f.write(f"Overall status: {status}\n")

    return all_within_tol


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconcile v1 vs v2 analysis outputs")
    parser.add_argument("--v1", required=True, help="Path to v1 results directory")
    parser.add_argument("--v2", required=True, help="Path to v2 results directory")
    parser.add_argument(
        "--tol", type=float, default=1e-8, help="Numerical tolerance for differences"
    )
    parser.add_argument(
        "--out", default="results/reconciliation_report/", help="Output directory"
    )

    args = parser.parse_args(argv)

    v1_dir = Path(args.v1)
    v2_dir = Path(args.v2)
    out_dir = Path(args.out)

    if not v1_dir.exists():
        print(f"V1 directory {v1_dir} does not exist")
        return 1
    if not v2_dir.exists():
        print(f"V2 directory {v2_dir} does not exist")
        return 1

    # Find files
    v1_csvs = find_csv_files(v1_dir)
    v2_csvs = find_csv_files(v2_dir)
    v1_figures = find_figure_files(v1_dir)
    v2_figures = find_figure_files(v2_dir)

    # Compare CSVs
    csv_comparisons = {}
    common_csvs = set(v1_csvs.keys()) & set(v2_csvs.keys())

    out_dir.mkdir(parents=True, exist_ok=True)

    for csv_name in common_csvs:
        print(f"Comparing CSV: {csv_name}")
        comp = compare_csvs(v1_csvs[csv_name], v2_csvs[csv_name], args.tol)
        csv_comparisons[csv_name] = comp
        write_csv_diff(out_dir, csv_name, comp)

    # Report unmatched CSVs
    v1_only = set(v1_csvs.keys()) - set(v2_csvs.keys())
    v2_only = set(v2_csvs.keys()) - set(v1_csvs.keys())
    if v1_only:
        print(f"V1-only CSVs: {v1_only}")
    if v2_only:
        print(f"V2-only CSVs: {v2_only}")

    # Compare figures
    figure_comparisons = compare_figures(v1_figures, v2_figures)

    # Write summary
    all_within_tol = write_summary(
        out_dir, csv_comparisons, figure_comparisons, args.tol
    )

    print(f"Reconciliation report written to {out_dir}")

    return 0 if all_within_tol else 1


if __name__ == "__main__":
    sys.exit(main())
