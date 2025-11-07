"""Compute cost-effectiveness acceptability frontier (CEAF) curves from PSA data."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis_core.io import load_analysis_inputs, assert_strategy_presence
from analysis_core.nmb import argmax_with_tiebreak
from analysis_core.plotting import figure_context, save_multiformat
from analysis_v2.publication import (
    ceaf_caption,
    write_ceaf_table,
    write_caption_file,
    display_name,
)
from utils import set_seed

DEFAULT_STRATEGIES_YAML = Path(__file__).resolve().parent.parent / "config" / "strategies.yml"
ORAL_KETAMINE_LABEL = "PO-KA"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute CEAF curves from PSA draws")
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
    parser.add_argument("--lambda-min", dest="lambda_min", type=float, required=True)
    parser.add_argument("--lambda-max", dest="lambda_max", type=float, required=True)
    parser.add_argument("--lambda-step", dest="lambda_step", type=float, required=True)
    parser.add_argument(
        "--outdir",
        type=Path,
        required=True,
        help="Directory to store CEAF outputs",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
        help="Random seed for reproducibility (default: 12345)",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------


def build_lambda_grid(lambda_min: float, lambda_max: float, lambda_step: float) -> np.ndarray:
    if lambda_step <= 0:
        raise ValueError("--lambda-step must be positive")
    if lambda_max < lambda_min:
        raise ValueError("--lambda-max must be greater than or equal to --lambda-min")

    n_steps = int(np.floor((lambda_max - lambda_min) / lambda_step + 1e-9))
    grid = lambda_min + lambda_step * np.arange(n_steps + 1)
    if grid.size == 0 or grid[-1] < lambda_max:
        grid = np.append(grid, lambda_max)
    return np.round(grid, 8)


def ordered_strategies(config_strategies: List[str], table_strategies: Iterable[str]) -> List[str]:
    ordered = [s for s in config_strategies if s in table_strategies]
    for strategy in table_strategies:
        if strategy not in ordered:
            ordered.append(strategy)
    return ordered


def choose_expected_optimal(expected_nmb: pd.Series, strategies_order: List[str], focal: Optional[str] = None) -> str:
    max_value = expected_nmb.max()
    candidates = [s for s in strategies_order if np.isclose(expected_nmb.get(s, -np.inf), max_value)]
    if not candidates:
        raise RuntimeError("Unable to determine expected-optimal strategy")
    if focal and focal in candidates:
        return focal
    return candidates[0]


def compute_ceaf(
    psa_table: pd.DataFrame,
    strategies: List[str],
    lambda_grid: Iterable[float],
    focal: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cost = psa_table.pivot(index="draw", columns="strategy", values="cost")[strategies]
    effect = psa_table.pivot(index="draw", columns="strategy", values="effect")[strategies]

    results_rows = []
    ceaf_rows = []

    for lam in lambda_grid:
        nmb = lam * effect - cost
        expected = nmb.mean(axis=0)
        optimal_draws = argmax_with_tiebreak(nmb, focal=focal)
        probabilities = optimal_draws.value_counts(normalize=True).reindex(strategies, fill_value=0.0)

        ceaf_strategy = choose_expected_optimal(expected, strategies, focal=focal)
        ceaf_probability = float(probabilities.loc[ceaf_strategy])
        ceaf_expected_nmb = float(expected.loc[ceaf_strategy])

        for strategy in strategies:
            results_rows.append(
                {
                    "lambda": float(lam),
                    "strategy": strategy,
                    "probability_optimal": float(probabilities.loc[strategy]),
                    "expected_nmb": float(expected.loc[strategy]),
                    "ceaf_strategy": ceaf_strategy,
                    "ceaf_probability": ceaf_probability,
                    "ceaf_expected_nmb": ceaf_expected_nmb,
                }
            )

        ceaf_rows.append(
            {
                "lambda": float(lam),
                "ceaf_strategy": ceaf_strategy,
                "ceaf_probability": ceaf_probability,
                "ceaf_expected_nmb": ceaf_expected_nmb,
            }
        )

    probabilities_df = pd.DataFrame(results_rows)
    ceaf_df = pd.DataFrame(ceaf_rows)
    return probabilities_df, ceaf_df


# ---------------------------------------------------------------------------
# Plotting & export
# ---------------------------------------------------------------------------


def plot_ceaf(
    probabilities_df: pd.DataFrame,
    ceaf_df: pd.DataFrame,
    strategies: List[str],
    perspective: str,
    outdir: Path,
    label_lookup: dict[str, str] | None = None,
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    pivot_prob = (
        probabilities_df.pivot_table(
            index="lambda", columns="strategy", values="probability_optimal", aggfunc="first"
        )
        .reindex(columns=strategies)
        .sort_index()
    )

    with figure_context(
        title=f"Cost-Effectiveness Acceptability Frontier – {perspective.replace('_', ' ').title()} Perspective",
        xlabel="Willingness-to-Pay Threshold ($/QALY)",
        ylabel="Probability Cost-Effective",
        figsize=(10, 6)
    ) as (fig, ax):
        # Publication-quality color palette
        intervention_colors = {
            'Usual care': '#2E2E2E',
            'ECT': '#1f77b4', 
            'ECT-KA': '#ff7f0e',
            'Therapy A': '#2ca02c', 
            'Therapy B': '#d62728',
            'Therapy C': '#9467bd',
            'Oral ketamine': '#8c564b',
            'Ketamine': '#e377c2',
            'Esketamine': '#7f7f7f',
            'Psilocybin': '#bcbd22'
        }
        
        # Fallback color cycle for unlisted strategies
        color_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
        strategy_colors = {}
        for i, strategy in enumerate(strategies):
            strategy_colors[strategy] = intervention_colors.get(strategy, color_cycle[i % len(color_cycle)])

        for strategy in strategies:
            label = (label_lookup or {}).get(strategy, strategy)
            ax.plot(
                pivot_prob.index,
                pivot_prob[strategy],
                label=label,
                linewidth=2.5,
                color=strategy_colors[strategy],
                alpha=0.8
            )

        ax.plot(
            ceaf_df["lambda"],
            ceaf_df["ceaf_probability"],
            color="black",
            linewidth=3.0,
            linestyle="--",
            label="CEAF (Frontier)",
            alpha=0.9
        )

        ax.set_ylim(0, 1.05)
        # Set reasonable x-axis range for better curve differentiation
        ax.set_xlim(0, 75000)  # Focus on relevant WTP range
        ax.grid(True, alpha=0.3)
        
        # Format x-axis as currency
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Enhanced legend
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, 
                 fancybox=True, shadow=True, fontsize=10)
        
        fig.tight_layout()
        filename = f"v2_ceaf_individual_{perspective.lower()}"
        save_multiformat(fig, outdir, filename, formats=['png', 'pdf', 'svg'], dpi=300)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    set_seed(args.seed)

    lambda_grid = build_lambda_grid(args.lambda_min, args.lambda_max, args.lambda_step)

    data = load_analysis_inputs(
        psa_path=args.psa,
        config_path=args.strategies_yaml,
        perspective=args.perspective,
        focal=ORAL_KETAMINE_LABEL,
        lambda_grid=lambda_grid,
    )

    # Check for focal strategy presence
    present_strategies, missing_strategies = assert_strategy_presence(
        data.table, args.perspective, [ORAL_KETAMINE_LABEL]
    )
    if ORAL_KETAMINE_LABEL not in present_strategies:
        args.outdir.mkdir(parents=True, exist_ok=True)
        skip_note = f"CEAF analysis skipped: focal strategy '{ORAL_KETAMINE_LABEL}' not found in PSA data for {args.perspective} perspective."
        (args.outdir / "SKIP").write_text(skip_note)
        print(skip_note)
        return

    strategies = ordered_strategies(data.config.strategies, data.table["strategy"].unique())
    if ORAL_KETAMINE_LABEL in data.table["strategy"].unique() and ORAL_KETAMINE_LABEL not in strategies:
        strategies.append(ORAL_KETAMINE_LABEL)

    probabilities_df, ceaf_df = compute_ceaf(
        psa_table=data.table,
        strategies=strategies,
        lambda_grid=lambda_grid,
        focal=ORAL_KETAMINE_LABEL if ORAL_KETAMINE_LABEL in strategies else None,
    )

    # Append human-readable labels alongside strategy identifiers
    label_map = {s: display_name(s, data.config) for s in strategies}
    probs_out = probabilities_df.copy()
    probs_out["display_strategy"] = probs_out["strategy"].map(label_map)
    args.outdir.mkdir(parents=True, exist_ok=True)
    probs_out.to_csv(args.outdir / "ceaf_results.csv", index=False)
    ceaf_out = ceaf_df.copy()
    ceaf_out["display_ceaf_strategy"] = ceaf_out["ceaf_strategy"].map(label_map).fillna(ceaf_out["ceaf_strategy"])
    ceaf_out.to_csv(args.outdir / "ceaf_summary.csv", index=False)

    write_ceaf_table(
        probabilities_df=probabilities_df,
        ceaf_df=ceaf_df,
        outdir=args.outdir,
        perspective=args.perspective,
        config=data.config,
        lambda_values=lambda_grid,
    )

    write_caption_file(
        args.outdir,
        "Figure_CEAF.caption.md",
        ceaf_caption(
            perspective=args.perspective,
            config=data.config,
            lambda_values=lambda_grid,
        ),
    )
    plot_ceaf(
        probabilities_df=probabilities_df,
        ceaf_df=ceaf_df,
        strategies=strategies,
        perspective=args.perspective,
        outdir=args.outdir,
        label_lookup=label_map,
    )

    print(f"CEAF outputs saved to {args.outdir}")


if __name__ == "__main__":
    main()
