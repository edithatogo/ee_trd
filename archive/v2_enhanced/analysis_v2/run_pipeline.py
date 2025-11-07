"""Batch runner for analysis_v2 cost-effectiveness outputs."""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis_core.io import StrategyConfig

CEAF_SCRIPT = PROJECT_ROOT / "analysis_v2" / "make_ceaf.py"
VBP_SCRIPT = PROJECT_ROOT / "analysis_v2" / "make_vbp_curve.py"
PRICE_PROB_SCRIPT = PROJECT_ROOT / "analysis_v2" / "make_price_prob_curves.py"
CE_PLANE_SCRIPT = PROJECT_ROOT / "analysis_v2" / "make_ce_plane.py"
EVPI_SCRIPT = PROJECT_ROOT / "analysis_v2" / "make_evpi.py"
# BIA_SCRIPT = PROJECT_ROOT / "analysis_v2" / "make_bia.py"  # Requires separate config
COMPARISON_SCRIPT = PROJECT_ROOT / "analysis_v2" / "make_comparison_plots.py"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "analysis_v2_defaults.yml"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full analysis_v2 pipeline")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Optional YAML file containing default parameters")
    parser.add_argument("--psa", type=Path, default=None, help="Override PSA CSV path")
    parser.add_argument("--strategies-yaml", type=Path, default=None, help="Override strategy configuration YAML path")
    parser.add_argument("--perspectives", default=None, help="Comma-separated list of perspectives to analyse")
    parser.add_argument("--lambda-min", dest="lambda_min", type=float, default=None)
    parser.add_argument("--lambda-max", dest="lambda_max", type=float, default=None)
    parser.add_argument("--lambda-step", dest="lambda_step", type=float, default=None)
    parser.add_argument("--lambda-single", dest="lambda_single", type=float, default=None, help="Single λ value used for price–probability curves")
    parser.add_argument("--price-min", dest="price_min", type=float, default=None)
    parser.add_argument("--price-max", dest="price_max", type=float, default=None)
    parser.add_argument("--price-step", dest="price_step", type=float, default=None)
    parser.add_argument("--outdir-root", dest="outdir_root", default=None, help="Root directory (string or template with {date}) for outputs")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--no-timestamp", action="store_true", help="Do not add timestamp to output directory")
    return parser.parse_args(argv)


def load_defaults(path: Path | None) -> Dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def resolve_param(args_value: Any, defaults: Dict[str, Any], key: str, required: bool = True):
    if args_value is not None:
        return args_value
    if key in defaults and defaults[key] is not None:
        return defaults[key]
    if required:
        raise ValueError(f"Missing required configuration value for '{key}'")
    return None


def normalise_perspectives(raw: Any) -> List[str]:
    if raw is None:
        raise ValueError("No perspectives supplied")
    if isinstance(raw, (list, tuple)):
        result = [str(item).strip() for item in raw if str(item).strip()]
    else:
        result = [part.strip() for part in str(raw).split(",") if part.strip()]
    if not result:
        raise ValueError("At least one perspective must be provided")
    return result


def determine_outdir_root(root_value: str, no_timestamp: bool = False) -> Path:
    if no_timestamp:
        rendered = root_value
    else:
        date_str = datetime.today().strftime("%Y%m%d")
        if "{date}" in root_value:
            rendered = root_value.format(date=date_str)
        else:
            rendered = f"{root_value.rstrip('/')}" + f"_{date_str}"
    return (PROJECT_ROOT / rendered).resolve()


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def ensure_scripts_exist() -> None:
    for script in (CEAF_SCRIPT, VBP_SCRIPT, PRICE_PROB_SCRIPT, CE_PLANE_SCRIPT, EVPI_SCRIPT, COMPARISON_SCRIPT):
        if not script.exists():
            raise FileNotFoundError(f"Required script missing: {script}")


def run_command(command: List[str]) -> None:
    print("→", " ".join(command))
    subprocess.run(command, check=True)


def main(argv: Iterable[str] | None = None) -> None:
    ensure_scripts_exist()
    args = parse_args(argv)
    defaults = load_defaults(args.config)

    psa_path = resolve_path(resolve_param(args.psa, defaults, "psa"))
    strategies_yaml = resolve_path(resolve_param(args.strategies_yaml, defaults, "strategies_yaml"))
    perspectives = normalise_perspectives(resolve_param(args.perspectives, defaults, "perspectives"))
    lambda_min = float(resolve_param(args.lambda_min, defaults, "lambda_min"))
    lambda_max = float(resolve_param(args.lambda_max, defaults, "lambda_max"))
    lambda_step = float(resolve_param(args.lambda_step, defaults, "lambda_step"))
    lambda_single = float(resolve_param(args.lambda_single, defaults, "lambda_single"))
    price_min = float(resolve_param(args.price_min, defaults, "price_min"))
    price_max = float(resolve_param(args.price_max, defaults, "price_max"))
    price_step = float(resolve_param(args.price_step, defaults, "price_step"))
    outdir_root_raw = str(resolve_param(args.outdir_root, defaults, "outdir_root"))
    seed = int(resolve_param(args.seed, defaults, "seed"))

    if not psa_path.exists():
        raise FileNotFoundError(f"PSA file not found at '{psa_path}'")
    if not strategies_yaml.exists():
        raise FileNotFoundError(f"Strategy YAML not found at '{strategies_yaml}'")

    if lambda_max < lambda_min:
        raise ValueError("lambda_max must be greater than or equal to lambda_min")
    if lambda_step <= 0:
        raise ValueError("lambda_step must be positive")
    if price_max < price_min:
        raise ValueError("price_max must be greater than or equal to price_min")
    if price_step <= 0:
        raise ValueError("price_step must be positive")

    strategy_config = StrategyConfig.from_yaml(strategies_yaml)
    focals = [strategy for strategy in strategy_config.strategies if strategy != strategy_config.base]
    focals_arg = ",".join(focals)

    base_outdir = determine_outdir_root(outdir_root_raw, args.no_timestamp)
    base_outdir.mkdir(parents=True, exist_ok=True)

    python_exec = sys.executable

    for perspective in perspectives:
        ceaf_out = base_outdir / "ceaf" / perspective
        vbp_out = base_outdir / "vbp" / perspective
        price_prob_out = base_outdir / "price_prob" / perspective
        ce_plane_out = base_outdir / "ce_plane" / perspective
        evpi_out = base_outdir / "evpi" / perspective

        commands = [
            [
                python_exec,
                str(CEAF_SCRIPT),
                "--psa",
                str(psa_path),
                "--strategies-yaml",
                str(strategies_yaml),
                "--perspective",
                perspective,
                "--lambda-min",
                str(lambda_min),
                "--lambda-max",
                str(lambda_max),
                "--lambda-step",
                str(lambda_step),
                "--outdir",
                str(ceaf_out),
                "--seed",
                str(seed),
            ],
            [
                python_exec,
                str(VBP_SCRIPT),
                "--psa",
                str(psa_path),
                "--strategies-yaml",
                str(strategies_yaml),
                "--perspective",
                perspective,
                "--focals",
                focals_arg,
                "--lambda-min",
                str(lambda_min),
                "--lambda-max",
                str(lambda_max),
                "--lambda-step",
                str(lambda_step),
                "--outdir",
                str(vbp_out),
                "--seed",
                str(seed),
            ],
        ]

        # Price probability curves for specific WTP values (30k, 45k, 50k)
        price_prob_lambdas = [30000, 45000, 50000]
        for lambda_val in price_prob_lambdas:
            price_prob_out_specific = price_prob_out / f"lambda_{int(lambda_val)}"
            commands.append([
                python_exec,
                str(PRICE_PROB_SCRIPT),
                "--psa",
                str(psa_path),
                "--strategies-yaml",
                str(strategies_yaml),
                "--perspective",
                perspective,
                "--lambda",
                str(lambda_val),
                "--price-min",
                str(price_min),
                "--price-max",
                str(price_max),
                "--price-step",
                str(price_step),
                "--outdir",
                str(price_prob_out_specific),
                "--seed",
                str(seed),
            ])

        commands.extend([
            [
                python_exec,
                str(CE_PLANE_SCRIPT),
                "--psa",
                str(psa_path),
                "--strategies-yaml",
                str(strategies_yaml),
                "--perspective",
                perspective,
                "--lambda",
                str(lambda_single),
                "--outdir",
                str(ce_plane_out),
                "--seed",
                str(seed),
            ],
            [
                python_exec,
                str(EVPI_SCRIPT),
                "--psa",
                str(psa_path),
                "--strategies-yaml",
                str(strategies_yaml),
                "--perspective",
                perspective,
                "--lambda-min",
                str(lambda_min),
                "--lambda-max",
                str(lambda_max),
                "--lambda-step",
                "2500",  # Coarser step for EVPI
                "--outdir",
                str(evpi_out),
                "--seed",
                str(seed),
            ],
        ])

        for command in commands:
            run_command(command)

    # Generate publication-quality comparison plots
    print("Generating publication-quality comparison plots...")
    comparison_outdir = base_outdir / "comparison_plots"
    comparison_outdir.mkdir(parents=True, exist_ok=True)
    
    comparison_command = [
        python_exec,
        str(COMPARISON_SCRIPT),
        "--psa",
        str(psa_path),
        "--strategies-yaml", 
        str(strategies_yaml),
        "--outdir",
        str(comparison_outdir),
        "--jurisdiction", 
        "AU",  # Default to AU, could be made configurable
        "--seed",
        str(seed),
    ]
    
    try:
        run_command(comparison_command)
        print("Comparison plots generated successfully!")
    except Exception as e:
        print(f"Warning: Failed to generate comparison plots: {e}")

    print(f"analysis_v2 outputs available under {base_outdir}")


if __name__ == "__main__":
    main()
