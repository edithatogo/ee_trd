#!/usr/bin/env python3
"""Check parameter cohesion across v2 analysis scripts."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)


def get_script_flags(script_path: Path) -> dict[str, dict]:
    """Get flags from script --help output."""
    try:
        result = subprocess.run(
            [sys.executable, script_path, "--help"],
            capture_output=True,
            text=True,
            cwd=script_path.parent.parent,
        )
        if result.returncode != 0:
            return {"error": result.stderr}

        help_text = result.stdout

        # Parse usage line to find required flags
        usage_lines = []
        in_usage = False
        for line in help_text.split("\n"):
            if line.startswith("usage:"):
                in_usage = True
                usage_lines.append(line)
            elif in_usage and (line.startswith(" ") or line.startswith("\t") or line.strip() == ""):
                usage_lines.append(line)
            elif in_usage and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                # Hit the next section
                break
        
        usage_text = " ".join(usage_lines).strip()
        
        required_flags = set()
        if usage_text:
            # Extract flags from usage line - required ones are not in [brackets]
            import re
            # Find all --flag patterns that are not inside [ ]
            parts = re.split(r'\[|\]', usage_text)
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Even parts are outside brackets (required)
                    flags_in_part = re.findall(r'(--[\w-]+)', part)
                    required_flags.update(flags_in_part)

        # Parse flags
        flags = {}
        lines = help_text.split("\n")
        current_flag = None

        for line in lines:
            # Look for --flag
            match = re.search(r"\s*(--[\w-]+)", line)
            if match:
                flag = match.group(1)
                current_flag = flag
                flags[flag] = {"description": line.strip(), "required": flag in required_flags}
            elif current_flag and line.strip().startswith(" "):
                # Continuation of description
                flags[current_flag]["description"] += " " + line.strip()

        return flags
    except Exception as e:
        return {"error": str(e)}


def check_lambda_flags(flags_dict: dict[str, dict]) -> tuple[bool, str]:
    """Check lambda flags are appropriate for each script type."""
    lambda_range_flags = ["--lambda-min", "--lambda-max", "--lambda-step"]
    lambda_single_flag = "--lambda"

    script_names = list(flags_dict.keys())
    if len(script_names) < 2:
        return True, "Only one script to check"

    # Check each script has appropriate lambda flags
    for script in script_names:
        if script not in flags_dict:
            continue

        has_range_flags = all(flag in flags_dict[script] for flag in lambda_range_flags)
        has_single_flag = lambda_single_flag in flags_dict[script]

        if not (has_range_flags or has_single_flag):
            return (
                False,
                f"{script} missing lambda flags (needs either --lambda or --lambda-min/max/step)",
            )

        if has_range_flags and has_single_flag:
            return (
                False,
                f"{script} has conflicting lambda flags (both single and range)",
            )

    return True, "Lambda flags appropriate for each script type"


def check_price_flags(flags_dict: dict[str, dict]) -> tuple[bool, str]:
    """Check price grid flags are identical."""
    price_flags = ["--price-min", "--price-max", "--price-step"]

    script_names = list(flags_dict.keys())

    # Check all scripts have the flags (not all may have price flags)
    scripts_with_price = []
    for script in script_names:
        if script in flags_dict and all(f in flags_dict[script] for f in price_flags):
            scripts_with_price.append(script)

    if len(scripts_with_price) < 2:
        return True, f"Only {len(scripts_with_price)} scripts have price flags"

    # Check defaults
    first_script = scripts_with_price[0]
    for flag in price_flags:
        first_desc = flags_dict[first_script][flag]["description"]
        for script in scripts_with_price[1:]:
            desc = flags_dict[script][flag]["description"]
            if desc != first_desc:
                return False, f"{flag} description differs: {first_script} vs {script}"

    return True, "Price flags consistent"


def check_plotting_usage(script_paths: list[Path]) -> tuple[bool, str]:
    """Check that scripts use analysis_core/plotting."""
    issues = []

    for script_path in script_paths:
        content = script_path.read_text()
        if "from analysis_core.plotting import" not in content:
            issues.append(
                f"{script_path.name} does not import from analysis_core/plotting"
            )

    return len(issues) == 0, (
        "; ".join(issues)
        if issues
        else "All scripts use analysis_core/plotting properly"
    )


def print_flags_table(flags_dict: dict[str, dict]) -> None:
    """Print a neat table of flags per script."""
    all_flags = set()
    for script_flags in flags_dict.values():
        if isinstance(script_flags, dict):
            all_flags.update(script_flags.keys())

    all_flags = sorted(all_flags)

    # Print header
    print("Flags Table:")
    print(f"{'Script':<20} {'Flag':<15} {'Type':<8} {'Description'}")
    print("-" * 80)

    for script_name, script_flags in flags_dict.items():
        if not isinstance(script_flags, dict):
            continue
        for flag in all_flags:
            if flag in script_flags:
                desc = script_flags[flag]["description"]
                flag_type = "Required" if script_flags[flag]["required"] else "Optional"
                print(f"{script_name:<20} {flag:<15} {flag_type:<8} {desc}")
            else:
                print(f"{script_name:<20} {flag:<15} {'Missing':<8}")


def main(argv: Iterable[str] | None = None) -> int:
    scripts = [
        "analysis_v2/make_ceaf.py",
        "analysis_v2/make_vbp_curve.py",
        "analysis_v2/make_price_prob_curves.py",
    ]

    script_paths = [Path(__file__).parent.parent / script for script in scripts]

    # Check plotting usage
    plotting_ok, plotting_msg = check_plotting_usage(script_paths)
    print(f"Plotting check: {'PASS' if plotting_ok else 'FAIL'} - {plotting_msg}")

    # Get flags for each script
    flags_dict = {}
    for script_path in script_paths:
        flags = get_script_flags(script_path)
        flags_dict[script_path.name] = flags

    # Check lambda flags
    lambda_ok, lambda_msg = check_lambda_flags(flags_dict)
    print(f"Lambda flags: {'PASS' if lambda_ok else 'FAIL'} - {lambda_msg}")

    # Check price flags
    price_ok, price_msg = check_price_flags(flags_dict)
    print(f"Price flags: {'PASS' if price_ok else 'FAIL'} - {price_msg}")

    # Print table
    print_flags_table(flags_dict)

    # Overall result
    all_ok = plotting_ok and lambda_ok and price_ok
    print(f"\nOverall: {'PASS' if all_ok else 'FAIL'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
