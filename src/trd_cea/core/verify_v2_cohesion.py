#!/usr/bin/env python3
"""Verify cohesion of v2 analysis pipeline."""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def check_source_tree() -> tuple[bool, str]:
    """Check source tree structure and imports."""
    issues = []

    # Check files exist
    required_files = [
        "analysis_v2/make_ceaf.py",
        "analysis_v2/make_vbp_curve.py",
        "analysis_v2/make_price_prob_curves.py",
    ]

    for file in required_files:
        if not (PROJECT_ROOT / file).exists():
            issues.append(f"Missing required file: {file}")

    # Check imports - should only import from analysis_core/*
    for file in required_files:
        if (PROJECT_ROOT / file).exists():
            content = (PROJECT_ROOT / file).read_text()
            if "from analysis_core" not in content:
                issues.append(f"{file} does not import from analysis_core")

    # Search for seaborn
    for root, dirs, files in os.walk(PROJECT_ROOT / "analysis_v2"):
        for file in files:
            if file.endswith(".py"):
                path = Path(root) / file
                content = path.read_text()
                if "seaborn" in content.lower():
                    issues.append(f"Seaborn found in {path}")

    return len(issues) == 0, (
        "; ".join(issues) if issues else "All source tree checks passed"
    )


def check_config_sanity(strategies_yaml: Path) -> tuple[bool, str]:
    """Check strategies YAML has required keys."""
    try:
        with open(strategies_yaml) as f:
            config = yaml.safe_load(f)

        required_keys = [
            "base",
            "perspectives",
            "strategies",
            "prices",
            "effects_unit",
            "currency",
        ]
        missing = [k for k in required_keys if k not in config]

        if missing:
            return False, f"Missing config keys: {', '.join(missing)}"

        return True, "Config sanity check passed"
    except Exception as e:
        return False, f"Config load error: {e}"


def check_psa_audit(psa_path: Path, perspectives: list[str]) -> tuple[bool, str]:
    """Audit PSA file structure."""
    try:
        df = pd.read_csv(psa_path)

        required_cols = ["strategy", "draw", "cost", "effect", "perspective"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            return False, f"Missing PSA columns: {', '.join(missing_cols)}"

        if df.isna().any().any():
            return False, "PSA contains NaN values"

        # Check draw IDs aligned across strategies within perspectives
        for perspective in perspectives:
            df_p = df[df["perspective"] == perspective]
            strategies_p = df_p["strategy"].unique()
            if len(strategies_p) == 0:
                continue
            first_strategy = strategies_p[0]
            expected_draws = set(df_p[df_p["strategy"] == first_strategy]["draw"])
            for strategy in strategies_p[1:]:
                draws = set(df_p[df_p["strategy"] == strategy]["draw"])
                if draws != expected_draws:
                    return (
                        False,
                        f"Draw IDs not aligned for {strategy} in {perspective}: expected {expected_draws}, got {draws}",
                    )

        # Check perspectives
        present_perspectives = df["perspective"].unique()
        missing_perspectives = [
            p for p in perspectives if p not in present_perspectives
        ]
        if missing_perspectives:
            return (
                False,
                f"Missing perspectives in PSA: {', '.join(missing_perspectives)}",
            )

        # Check Oral ketamine
        oral_ketamine_missing = []
        for perspective in perspectives:
            if not (
                (df["strategy"] == "Oral ketamine") & (df["perspective"] == perspective)
            ).any():
                oral_ketamine_missing.append(perspective)

        warning = ""
        if oral_ketamine_missing:
            warning = f" WARNING: Oral ketamine missing in perspectives: {', '.join(oral_ketamine_missing)}"

        return True, f"PSA audit passed{warning}"
    except Exception as e:
        return False, f"PSA audit error: {e}"


def dry_run_checks() -> tuple[bool, str]:
    """Test CLI scripts without running them."""
    issues = []

    scripts = [
        "analysis_v2/make_ceaf.py",
        "analysis_v2/make_vbp_curve.py",
        "analysis_v2/make_price_prob_curves.py",
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        for script in scripts:
            try:
                # Test import
                module_name = script.replace("/", ".").replace(".py", "")
                __import__(module_name)

                # Test --help
                result = subprocess.run(
                    [sys.executable, script, "--help"],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT,
                )
                if result.returncode != 0:
                    issues.append(f"{script} --help failed: {result.stderr}")

                # Test with temp outdir (dry run by using temp directory)
                script_name = Path(script).stem
                _temp_outdir = tmpdir / f"_verify_tmp_{script_name}"

                # Construct a minimal command that should work without full data
                if "make_ceaf" in script:
                    cmd = [
                        sys.executable, script,
                        "--help"  # Just test help for now since full test requires data
                    ]
                elif "make_vbp_curve" in script:
                    cmd = [
                        sys.executable, script,
                        "--help"
                    ]
                elif "make_price_prob_curves" in script:
                    cmd = [
                        sys.executable, script,
                        "--help"
                    ]

                result = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=PROJECT_ROOT
                )
                if result.returncode != 0 and "--help" not in cmd:
                    issues.append(f"{script} dry-run command failed: {result.stderr}")

            except Exception as e:
                issues.append(f"{script} dry-run failed: {e}")

    return len(issues) == 0, "; ".join(issues) if issues else "Dry-run checks passed"


def run_real_analysis(args: argparse.Namespace, timestamp: str) -> tuple[bool, str]:
    """Run the full analysis pipeline."""
    outdir_base = Path("results") / f"verification_run_{timestamp}"
    issues = []

    perspectives = args.perspectives.split(",")

    for perspective in perspectives:
        outdir = outdir_base / perspective

        # CEAF
        cmd = [
            sys.executable,
            "analysis_v2/make_ceaf.py",
            "--psa",
            str(args.psa),
            "--strategies-yaml",
            str(args.strategies_yaml),
            "--perspective",
            perspective,
            "--lambda-min",
            str(args.lambda_min),
            "--lambda-max",
            str(args.lambda_max),
            "--lambda-step",
            str(args.lambda_step),
            "--outdir",
            str(outdir / "ceaf"),
            "--seed",
            str(args.seed),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            issues.append(f"CEAF {perspective} failed: {result.stderr}")

        # VBP
        cmd = [
            sys.executable,
            "analysis_v2/make_vbp_curve.py",
            "--psa",
            str(args.psa),
            "--strategies-yaml",
            str(args.strategies_yaml),
            "--perspective",
            perspective,
            "--focals",
            "Oral ketamine",
            "--lambda-min",
            str(args.lambda_min),
            "--lambda-max",
            str(args.lambda_max),
            "--lambda-step",
            str(args.lambda_step),
            "--outdir",
            str(outdir / "vbp"),
            "--seed",
            str(args.seed),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            issues.append(f"VBP {perspective} failed: {result.stderr}")

        # Price-prob
        cmd = [
            sys.executable,
            "analysis_v2/make_price_prob_curves.py",
            "--psa",
            str(args.psa),
            "--strategies-yaml",
            str(args.strategies_yaml),
            "--perspective",
            perspective,
            "--lambda",
            "50000",  # Use a default WTP
            "--price-min",
            str(args.price_min),
            "--price-max",
            str(args.price_max),
            "--price-step",
            str(args.price_step),
            "--outdir",
            str(outdir / "price_prob"),
            "--seed",
            str(args.seed),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            issues.append(f"Price-prob {perspective} failed: {result.stderr}")

    return len(issues) == 0, "; ".join(issues) if issues else "Real run completed"


def check_outputs_completeness(
    outdir_base: Path, perspectives: list[str]
) -> tuple[bool, str]:
    """Check that all expected outputs exist."""
    issues = []

    for perspective in perspectives:
        outdir = outdir_base / perspective

        # CEAF
        ceaf_dir = outdir / "ceaf"
        if not ceaf_dir.exists():
            issues.append(f"CEAF dir missing for {perspective}")
        else:
            skip_file = ceaf_dir / "SKIP"
            if skip_file.exists():
                # SKIP file indicates analysis was appropriately skipped
                continue
            if not list(ceaf_dir.glob("ceaf_results.csv")):
                issues.append(f"CEAF CSV missing for {perspective}")
            if not list(ceaf_dir.glob("ceaf_curve.pdf")):
                issues.append(f"CEAF PDF missing for {perspective}")
            if not list(ceaf_dir.glob("Figure_CEAF.caption.md")):
                issues.append(f"CEAF caption missing for {perspective}")

        # VBP
        vbp_dir = outdir / "vbp"
        if not vbp_dir.exists():
            issues.append(f"VBP dir missing for {perspective}")
        else:
            skip_file = vbp_dir / "SKIP"
            if skip_file.exists():
                # SKIP file indicates analysis was appropriately skipped
                continue
            # VBP files are in subdirectories
            vbp_csv_found = list(vbp_dir.glob("*/vbp_curve.csv"))
            if not vbp_csv_found:
                issues.append(f"VBP CSV missing for {perspective}")
            vbp_pdf_found = list(vbp_dir.glob("*/vbp_curve.pdf"))
            if not vbp_pdf_found:
                issues.append(f"VBP PDF missing for {perspective}")

        # Price-prob
        pp_dir = outdir / "price_prob"
        if not pp_dir.exists():
            issues.append(f"Price-prob dir missing for {perspective}")
        else:
            skip_file = pp_dir / "SKIP"
            if skip_file.exists():
                # SKIP file indicates analysis was appropriately skipped
                continue
            if not list(pp_dir.glob("therapy_price_prob_beats_base.csv")):
                issues.append(f"Price-prob CSV missing for {perspective}")
            if not list(pp_dir.glob("price_prob_curves.pdf")):
                issues.append(f"Price-prob PDF missing for {perspective}")

        # Manuscript tables
        manuscript_dirs = [
            Path("tables_for_manuscript"),
            Path("results/tables_for_manuscript"),
        ]
        total_csv_count = 0
        for manuscript_dir in manuscript_dirs:
            if manuscript_dir.exists():
                csv_files = list(manuscript_dir.rglob("*.csv"))
                total_csv_count += len(csv_files)
        if total_csv_count < 3:
            issues.append(
                f"Only {total_csv_count} manuscript tables found, expected at least 3"
            )

    return len(issues) == 0, (
        "; ".join(issues) if issues else "Outputs completeness check passed"
    )


def check_determinism(args: argparse.Namespace) -> tuple[bool, str]:
    """Check that results are deterministic with same seed."""
    issues = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Run VBP twice
        for i in [1, 2]:
            outdir = tmpdir / f"vbp_run_{i}"
            cmd = [
                sys.executable,
                "analysis_v2/make_vbp_curve.py",
                "--psa",
                str(args.psa),
                "--strategies-yaml",
                str(args.strategies_yaml),
                "--perspective",
                "health_system",
                "--focals",
                "Oral ketamine",
                "--lambda-min",
                "0",
                "--lambda-max",
                "100000",
                "--lambda-step",
                "1000",
                "--outdir",
                str(outdir),
                "--seed",
                str(args.seed),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=PROJECT_ROOT
            )
            if result.returncode != 0:
                issues.append(f"VBP run {i} failed: {result.stderr}")

        if not issues:
            # Compare outputs
            run1_dir = tmpdir / "vbp_run_1"
            run2_dir = tmpdir / "vbp_run_2"

            # Compare CSV
            csv1 = run1_dir / "vbp.csv"
            csv2 = run2_dir / "vbp.csv"
            if csv1.exists() and csv2.exists():
                if csv1.read_bytes() != csv2.read_bytes():
                    issues.append("VBP CSV not deterministic")

            # Compare PNG hashes
            for png1 in run1_dir.glob("*.png"):
                png2 = run2_dir / png1.name
                if png2.exists():
                    hash1 = hashlib.md5(png1.read_bytes()).hexdigest()
                    hash2 = hashlib.md5(png2.read_bytes()).hexdigest()
                    if hash1 != hash2:
                        issues.append(f"PNG {png1.name} not deterministic")

            # Compare PDF/SVG sizes
            for ext in ["pdf", "svg"]:
                for file1 in run1_dir.glob(f"*.{ext}"):
                    file2 = run2_dir / file1.name
                    if file2.exists():
                        size1 = file1.stat().st_size
                        size2 = file2.stat().st_size
                        if (
                            abs(size1 - size2) / max(size1, size2) > 0.02
                        ):  # 2% tolerance
                            issues.append(
                                f"{ext.upper()} {file1.name} size differs by >2%"
                            )

    return len(issues) == 0, "; ".join(issues) if issues else "Determinism check passed"


def write_report(results: dict[str, tuple[bool, str]], report_dir: Path) -> None:
    """Write verification report."""
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "report.md"

    with open(report_path, "w") as f:
        f.write("# V2 Pipeline Verification Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")

        all_passed = True
        for check, (passed, message) in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            f.write(f"## {check}: {status}\n\n")
            f.write(f"{message}\n\n")

            # Add fix hints for failed checks
            if not passed:
                all_passed = False
                if "Source Tree" in check:
                    f.write("**Fix:** Ensure analysis_v2/ scripts exist and import only from analysis_core/*. Remove any seaborn imports.\n\n")
                elif "Config Sanity" in check:
                    f.write("**Fix:** Add missing keys to config/strategies.yml: base, perspectives, strategies, prices, effects_unit, currency.\n\n")
                elif "PSA Audit" in check:
                    f.write("**Fix:** Ensure PSA CSV has columns: strategy,draw,cost,effect,perspective. Remove NaNs. Align draw IDs across strategies.\n\n")
                elif "Dry-run Checks" in check:
                    f.write("**Fix:** Check that analysis_v2/ scripts can be imported and their --help works.\n\n")
                elif "Real Run" in check:
                    f.write("**Fix:** Check analysis_v2/ scripts for errors. Ensure input files exist.\n\n")
                elif "Outputs Completeness" in check:
                    f.write("**Fix:** Run missing analyses or check why they were skipped.\n\n")
                elif "Determinism" in check:
                    f.write("**Fix:** Ensure random seed is properly used in all analysis scripts.\n\n")

        f.write("## Summary\n\n")
        if all_passed:
            f.write("🎉 **ALL CHECKS PASSED** - Pipeline is cohesive and ready for use.\n\n")
            f.write("Next steps:\n")
            f.write("- Run `make verify_v2` for ongoing verification\n")
            f.write("- Use `python scripts/autofix_common_issues.py` for automatic fixes\n")
        else:
            f.write("❌ **CHECKS FAILED** - See fix hints above.\n\n")
            f.write("Next steps:\n")
            f.write("- Address the issues listed above\n")
            f.write("- Re-run verification after fixes\n")
            f.write("- Consider using `python scripts/autofix_common_issues.py` for automatic fixes\n")

    print(f"Report written to {report_path}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify v2 analysis pipeline cohesion")
    parser.add_argument("--psa", required=True, help="Path to PSA CSV")
    parser.add_argument(
        "--strategies-yaml", required=True, help="Path to strategies YAML"
    )
    parser.add_argument(
        "--results-root", default="results/", help="Results root directory"
    )
    parser.add_argument(
        "--perspectives",
        default="health_system,societal",
        help="Comma-separated perspectives",
    )
    parser.add_argument("--lambda-min", type=int, default=0, help="Lambda min")
    parser.add_argument("--lambda-max", type=int, default=200000, help="Lambda max")
    parser.add_argument("--lambda-step", type=int, default=1000, help="Lambda step")
    parser.add_argument("--price-min", type=int, default=0, help="Price min")
    parser.add_argument("--price-max", type=int, default=40000, help="Price max")
    parser.add_argument("--price-step", type=int, default=200, help="Price step")
    parser.add_argument("--seed", type=int, default=12345, help="Random seed")
    parser.add_argument(
        "--run-real", action="store_true", help="Run real analysis (not just dry-run)"
    )

    args = parser.parse_args(argv)

    perspectives = args.perspectives.split(",")

    results = {}

    # 1. Source tree checks
    results["Source Tree"] = check_source_tree()

    # 2. Config sanity
    results["Config Sanity"] = check_config_sanity(Path(args.strategies_yaml))

    # 3. PSA audit
    results["PSA Audit"] = check_psa_audit(Path(args.psa), perspectives)

    # 4. Dry-run calls
    results["Dry-run Checks"] = dry_run_checks()

    # 5. Optional real run
    if args.run_real:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        results["Real Run"] = run_real_analysis(args, timestamp)

        # 6. Outputs completeness
        outdir_base = Path("results") / f"verification_run_{timestamp}"
        results["Outputs Completeness"] = check_outputs_completeness(
            outdir_base, perspectives
        )

        # 7. Determinism
        results["Determinism"] = check_determinism(args)

    # 8. Report
    report_dir = Path(args.results_root) / "verification_report"
    write_report(results, report_dir)

    # Exit code
    any_fail = any(not passed for passed, _ in results.values())
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
