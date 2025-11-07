#!/usr/bin/env python3
"""Generate publication-ready cost-effectiveness planes using PSA draws.

The script intentionally avoids overwriting existing plots. It loads probabilistic
sensitivity analysis (PSA) outputs, plots incremental costs vs incremental QALYs
for each strategy, and saves the figure to a user-specified path.
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

from trd_cea.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

# Project structure helpers -------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_ROOT / "results"

# Plot look-and-feel --------------------------------------------------------
PALETTE = ["#023047", "#219EBC", "#FFB703", "#FB8500"]
MARKERS = ["o", "s", "^", "D"]
WTP_THRESHOLDS = [0, 25000, 50000, 75000, 100000]


def candiate_psa_paths(country: str, perspective: str) -> Iterable[Path]:
    """Return possible PSA output paths ordered by preference."""
    filenames = [
        f"psa_results_{country}_{perspective}.csv",
        f"psa_results_{country}.csv",
    ]

    for directory in (RESULTS_DIR, SCRIPT_DIR):
        for name in filenames:
            yield directory / name


def load_psa(country: str, perspective: str) -> pd.DataFrame:
    """Load PSA draws and normalise column names.

    The function searches both the top-level ``results`` directory and the
    ``scripts`` directory for perspective-specific PSA outputs before falling
    back to the aggregate file name.
    """
    for path in candiate_psa_paths(country, perspective):
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

    return psa


def currency_label(country: str) -> str:
    return "AUD" if country.upper() == "AU" else "NZD"


def plot_ce_plane(psa: pd.DataFrame, country: str, perspective: str, output: Path) -> None:
    """Create a combined CE plane using raw PSA draws."""
    output.parent.mkdir(parents=True, exist_ok=True)

    strategies = list(psa["strategy"].unique())
    colour_cycle = PALETTE * ((len(strategies) // len(PALETTE)) + 1)
    marker_cycle = MARKERS * ((len(strategies) // len(MARKERS)) + 1)

    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)

    for colour, marker, strategy in zip(colour_cycle, marker_cycle, strategies):
        subset = psa[psa["strategy"] == strategy]
        ax.scatter(
            subset["incremental_qalys"],
            subset["incremental_cost"],
            s=18,
            alpha=0.30,
            color=colour,
            marker=marker,
            linewidths=0,
            label=strategy,
        )

    # Threshold lines -------------------------------------------------------
    qaly_min = psa["incremental_qalys"].min()
    qaly_max = psa["incremental_qalys"].max()
    qaly_grid = np.linspace(qaly_min, qaly_max, 200)

    for wtp in WTP_THRESHOLDS:
        ax.plot(
            qaly_grid,
            wtp * qaly_grid,
            linestyle="--",
            linewidth=1.0,
            alpha=0.6,
            color="#6c757d",
        )

    # Quadrant reference lines ----------------------------------------------
    ax.axhline(0, color="#343a40", linewidth=0.8)
    ax.axvline(0, color="#343a40", linewidth=0.8)

    # Labels / formatting ---------------------------------------------------
    currency = currency_label(country)
    ax.set_xlabel("Incremental QALYs")
    ax.set_ylabel(f"Incremental cost ({currency})")
    ax.set_title(
        "Cost-effectiveness plane\n"
        f"{country.upper()} – {perspective.capitalize()} perspective"
    )

    # Axis limits with padding
    q_padding = (qaly_max - qaly_min) * 0.1 or 0.05
    c_min = psa["incremental_cost"].min()
    c_max = psa["incremental_cost"].max()
    c_padding = (c_max - c_min) * 0.1 or 500

    ax.set_xlim(qaly_min - q_padding, qaly_max + q_padding)
    ax.set_ylim(c_min - c_padding, c_max + c_padding)

    ax.grid(True, alpha=0.2)
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create CE plane from PSA draws")
    parser.add_argument("--country", choices=["AU", "NZ"], required=True)
    parser.add_argument("--perspective", choices=["healthcare", "societal"], required=True)
    parser.add_argument("--output", type=Path, required=True, help="Path to save the PNG")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    psa = load_psa(args.country, args.perspective)
    plot_ce_plane(psa, args.country, args.perspective, args.output)


if __name__ == "__main__":
    main()
