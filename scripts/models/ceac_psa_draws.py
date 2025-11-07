#!/usr/bin/env python3
"""Generate cost-effectiveness acceptability curves (CEACs) from PSA draws.

The script reads PSA outputs, computes the probability that each non-ECT strategy
is cost-effective across a grid of willingness-to-pay (WTP) thresholds, and saves
high-resolution plots without overwriting existing images.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_ROOT / "results"

STRATEGIES = ["Ketamine", "Esketamine", "Psilocybin"]
PALETTE = {
    "Ketamine": "#023047",
    "Esketamine": "#219EBC",
    "Psilocybin": "#FFB703",
}


def psa_candidate_paths(country: str, perspective: str) -> Iterable[Path]:
    filenames = [
        f"psa_results_{country}_{perspective}.csv",
        f"psa_results_{country}.csv",
    ]
    for directory in (RESULTS_DIR, SCRIPT_DIR):
        for name in filenames:
            yield directory / name


def load_psa(country: str, perspective: str) -> pd.DataFrame:
    for path in psa_candidate_paths(country, perspective):
        if path.exists():
            psa = pd.read_csv(path)
            break
    else:
        raise FileNotFoundError(
            "Could not locate PSA results for "
            f"country='{country}', perspective='{perspective}'."
        )

    column_map = {
        "inc_cost": "incremental_cost",
        "inc_qalys": "incremental_qalys",
        "incremental_cost": "incremental_cost",
        "incremental_qaly": "incremental_qalys",
    }
    psa = psa.rename(columns=column_map)

    required = {"strategy", "incremental_cost", "incremental_qalys"}
    missing = required - set(psa.columns)
    if missing:
        raise KeyError(
            "PSA results are missing required columns: " + ", ".join(sorted(missing))
        )

    psa = psa[psa["strategy"].isin(STRATEGIES)].copy()
    psa = psa.replace([np.inf, -np.inf], np.nan).dropna(subset=["incremental_cost", "incremental_qalys"])
    return psa


def wtp_grid(country: str) -> np.ndarray:
    if country.upper() == "AU":
        return np.linspace(0, 100_000, 201)
    return np.linspace(0, 60_000, 181)


def compute_ceac(psa: pd.DataFrame, country: str) -> pd.DataFrame:
    wtp_values = wtp_grid(country)
    records = []
    for strategy in STRATEGIES:
        subset = psa[psa["strategy"] == strategy]
        if subset.empty:
            continue
        dq = subset["incremental_qalys"].values
        dc = subset["incremental_cost"].values
        for wtp in wtp_values:
            net_benefit = wtp * dq - dc
            prob_ce = np.mean(net_benefit > 0)
            records.append({"strategy": strategy, "wtp": wtp, "probability": prob_ce})
    return pd.DataFrame(records)


def plot_ceac(df: pd.DataFrame, country: str, perspective: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    for strategy in STRATEGIES:
        curve = df[df["strategy"] == strategy]
        if curve.empty:
            continue
        ax.plot(
            curve["wtp"],
            curve["probability"],
            label=strategy,
            color=PALETTE.get(strategy, "#6c757d"),
            linewidth=2.0,
        )

    currency = "AUD" if country.upper() == "AU" else "NZD"
    ax.set_xlabel(f"WTP ({currency} per QALY)")
    ax.set_ylabel("Probability cost-effective vs ECT")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.2)
    ax.legend(frameon=False)
    ax.set_title(
        "Cost-effectiveness acceptability curve\n"
        f"{country.upper()} – {perspective.capitalize()} perspective"
    )

    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CEAC from PSA results")
    parser.add_argument("--country", choices=["AU", "NZ"], required=True)
    parser.add_argument("--perspective", choices=["healthcare", "societal"], required=True)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination PNG path; parent folders will be created if needed.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    psa = load_psa(args.country, args.perspective)
    ceac = compute_ceac(psa, args.country)
    plot_ceac(ceac, args.country, args.perspective, args.output)


if __name__ == "__main__":
    main()
