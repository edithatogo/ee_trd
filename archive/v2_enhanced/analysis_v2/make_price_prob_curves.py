"""Compute price–probability curves against the base strategy using PSA draws."""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis_core.grids import price_grid
from analysis_core.io import load_analysis_inputs, assert_strategy_presence
from analysis_core.plotting import (
    add_vertical_reference,
    figure_context,
    save_multiformat,
    write_caption,
    ensure_legend,
)
from analysis_v2.publication import price_probability_caption
from utils import set_seed

DEFAULT_STRATEGIES_YAML = PROJECT_ROOT / "config" / "strategies.yml"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Price–probability curves vs base strategy")
    parser.add_argument("--psa", type=Path, required=True, help="Path to PSA CSV file")
    parser.add_argument(
        "--strategies-yaml",
        type=Path,
        default=DEFAULT_STRATEGIES_YAML,
        help="Strategy configuration YAML (defaults to config/strategies.yml)",
    )
    parser.add_argument(
        "--perspective",
        choices=["health_system", "societal"],
        required=True,
        help="Perspective to analyse",
    )
    parser.add_argument("--lambda", dest="wtp", type=float, required=True)
    parser.add_argument("--price-min", dest="price_min", type=float, required=True)
    parser.add_argument("--price-max", dest="price_max", type=float, required=True)
    parser.add_argument("--price-step", dest="price_step", type=float, required=True)
    parser.add_argument(
        "--outdir",
        type=Path,
        required=True,
        help="Directory to store outputs",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
        help="Random seed for reproducibility (default 12345)",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def compute_probabilities(
    psa_table: pd.DataFrame,
    base: str,
    therapies: List[str],
    price_values: np.ndarray,
    wtp: float,
    prices_config: Dict[str, float],
) -> pd.DataFrame:
    pivot_cost = psa_table.pivot(index="draw", columns="strategy", values="cost")
    pivot_effect = psa_table.pivot(index="draw", columns="strategy", values="effect")

    missing = [strategy for strategy in therapies + [base] if strategy not in pivot_cost.columns]
    if missing:
        raise ValueError(f"Missing strategies in PSA table: {missing}")

    base_cost = pivot_cost[base].to_numpy()
    base_effect = pivot_effect[base].to_numpy()

    records = []
    for therapy, price in itertools.product(therapies, price_values):
        cost = pivot_cost[therapy].to_numpy()
        effect = pivot_effect[therapy].to_numpy()

        if therapy not in prices_config:
            raise KeyError(f"Strategy '{therapy}' missing price entry in configuration")
        baseline_price = float(prices_config[therapy])
        k_component = cost - baseline_price
        adjusted_cost = k_component + price

        nmb_therapy = wtp * effect - adjusted_cost
        nmb_base = wtp * base_effect - base_cost
        probability = float(np.mean(nmb_therapy > nmb_base))
        records.append({"therapy": therapy, "price": float(price), "prob_beats_base": probability})

    result = pd.DataFrame(records)
    result.sort_values(["therapy", "price"], inplace=True)
    result.reset_index(drop=True, inplace=True)
    return result


# ---------------------------------------------------------------------------
# Plotting & export
# ---------------------------------------------------------------------------


def plot_curves(
    probabilities: pd.DataFrame,
    price_values: np.ndarray,
    therapies: List[str],
    prices_config: Dict[str, float],
    perspective: str,
    outdir: Path,
    label_lookup: Dict[str, str] | None = None,
) -> Path:
    with figure_context(
        title=f"Price–probability curves vs {perspective} base",
        xlabel="Price (currency units)",
        ylabel="Probability beats base",
    ) as (fig, ax):
        palette = plt.rcParams['axes.prop_cycle'].by_key().get('color', None)
        color_iter = itertools.cycle(palette if palette else ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])

        for therapy in therapies:
            segment = probabilities[probabilities["therapy"] == therapy]
            segment = segment.sort_values("price")
            color = next(color_iter)
            label = (label_lookup or {}).get(therapy, therapy)
            ax.plot(
                segment["price"],
                segment["prob_beats_base"],
                label=label,
                linewidth=2.0,
                color=color,
            )
            if therapy in prices_config:
                add_vertical_reference(
                    ax,
                    prices_config[therapy],
                    label=f"{label} current price",
                    color=color,
                )

        ax.set_ylim(0, 1)
        ensure_legend(ax, frameon=False)
        fig.tight_layout()
        filename = f"v2_priceprob_individual_{perspective.lower()}"
        artifacts = save_multiformat(fig, outdir, filename)
    return artifacts.paths[0]



def export_probabilities(probabilities: pd.DataFrame, outdir: Path, label_lookup: Dict[str, str] | None = None) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    output_path = outdir / "therapy_price_prob_beats_base.csv"
    df = probabilities.copy()
    if label_lookup:
        df["display_therapy"] = df["therapy"].map(label_lookup)
    df.to_csv(output_path, index=False)
    return output_path


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    set_seed(args.seed)

    price_values = price_grid(args.price_min, args.price_max, args.price_step)

    psa_data = load_analysis_inputs(
        psa_path=args.psa,
        config_path=args.strategies_yaml,
        perspective=args.perspective,
        lambda_grid=[args.wtp],
    )

    base_strategy = psa_data.config.base
    available_strategies = [
        strategy for strategy in psa_data.config.strategies if strategy in psa_data.table["strategy"].unique()
    ]
    therapies = [strategy for strategy in available_strategies if strategy != base_strategy]

    # Check for base strategy and therapies presence
    required_strategies = [base_strategy] + therapies
    present_strategies, missing_strategies = assert_strategy_presence(
        psa_data.table, args.perspective, required_strategies
    )
    if base_strategy not in present_strategies:
        args.outdir.mkdir(parents=True, exist_ok=True)
        skip_note = f"Price-probability analysis skipped: base strategy '{base_strategy}' not found in PSA data for {args.perspective} perspective."
        (args.outdir / "SKIP").write_text(skip_note)
        print(skip_note)
        return
    if not therapies or all(t not in present_strategies for t in therapies):
        args.outdir.mkdir(parents=True, exist_ok=True)
        skip_note = f"Price-probability analysis skipped: no therapy strategies found in PSA data for {args.perspective} perspective. Missing: {', '.join(missing_strategies)}"
        (args.outdir / "SKIP").write_text(skip_note)
        print(skip_note)
        return

    # Filter therapies to only present ones
    therapies = [t for t in therapies if t in present_strategies]

    probabilities = compute_probabilities(
        psa_table=psa_data.table,
        base=base_strategy,
        therapies=therapies,
        price_values=price_values,
        wtp=args.wtp,
        prices_config=psa_data.config.prices,
    )
    label_map = {s: (psa_data.config.labels.get(s, s)) for s in therapies + [base_strategy]}
    export_probabilities(probabilities, args.outdir, label_lookup=label_map)
    plot_curves(
        probabilities=probabilities,
        price_values=price_values,
        therapies=therapies,
        prices_config=psa_data.config.prices,
        perspective=args.perspective,
        outdir=args.outdir,
        label_lookup=label_map,
    )
    write_caption(
        outdir=args.outdir,
        filename="Figure_PriceProb.caption.md",
        text=price_probability_caption(
            perspective=args.perspective,
            config=psa_data.config,
            lambda_value=args.wtp,
            price_values=price_values,
        ),
    )

    print(f"Price–probability outputs saved to {args.outdir}")


if __name__ == "__main__":
    main()
