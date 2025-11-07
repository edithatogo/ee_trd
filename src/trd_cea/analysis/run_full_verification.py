#!/usr/bin/env python3
"""
Run full verification suite for v2 analysis pipeline.

This script executes the complete verification workflow:
1. Smoke test pipeline
2. CI/code quality checks  
3. V2 pipeline verification

Captures all output to results/verification_report/combined.log
and provides final PASS/FAIL summary with links to reports.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
VERIFICATION_DIR = RESULTS_DIR / "verification_report"
LOG_FILE = VERIFICATION_DIR / "combined.log"


def run_command(cmd: List[str], description: str) -> Tuple[int, str, str]:
    """Run a command and capture output."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after 600 seconds: {' '.join(cmd)}"
    except Exception as e:
        return -1, "", f"Command failed with exception: {e}"


def log_output(description: str, returncode: int, stdout: str, stderr: str) -> None:
    """Log command output to file and console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{timestamp}] {description}\n")
        f.write(f"Return code: {returncode}\n")
        f.write('='*80 + '\n')
        
        if stdout:
            f.write("STDOUT:\n")
            f.write(stdout)
            f.write("\n")
        
        if stderr:
            f.write("STDERR:\n") 
            f.write(stderr)
            f.write("\n")
    
    # Also print to console
    if returncode != 0:
        print(f"❌ FAILED: {description}")
        if stderr:
            print(f"Error: {stderr.strip()}")
    else:
        print(f"✅ PASSED: {description}")


def main() -> int:
    """Run the full verification suite."""
    # Ensure output directory exists
    VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize log file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("w", encoding="utf-8") as f:
        f.write(f"Full Verification Suite - Started at {timestamp}\n")
        f.write("="*80 + "\n")
    
    print("🚀 Starting Full Verification Suite")
    print(f"📝 Logging to: {LOG_FILE}")
    
    # Define verification steps
    steps = [
        (
            ["make", "smoke_oral_ketamine"],
            "Smoke Test Pipeline"
        ),
        (
            ["make", "ci_v2"],
            "CI/Code Quality Checks"
        ),
        (
            ["make", "verify_v2"],
            "V2 Pipeline Verification"
        )
    ]
    
    results = []
    
    for cmd, description in steps:
        returncode, stdout, stderr = run_command(cmd, description)
        log_output(description, returncode, stdout, stderr)
        results.append((description, returncode == 0))
    
    # Generate summary
    print(f"\n{'='*80}")
    print("📊 VERIFICATION SUMMARY")
    print('='*80)
    
    all_passed = True
    for description, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {description}")
        if not passed:
            all_passed = False
    
    print(f"\n{'🎉' if all_passed else '💥'} OVERALL RESULT: {'PASS' if all_passed else 'FAIL'}")
    
    # Links to reports
    print("\n📋 Report Links:")
    print(f"   📄 Combined Log: {LOG_FILE}")
    
    # Check for individual reports
    report_files = [
        ("V2 Cohesion Report", VERIFICATION_DIR / "report.md"),
        ("Reconciliation Report", RESULTS_DIR / "reconciliation_report" / "report.md"),
        ("Publication Readiness", RESULTS_DIR / f"feat_oral_ketamine_{datetime.today().strftime('%Y%m%d')}" / "publication_readiness_checklist.md")
    ]
    
    for name, path in report_files:
        if path.exists():
            print(f"   📄 {name}: {path}")
        else:
            print(f"   ⚠️  {name}: Not found ({path})")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())