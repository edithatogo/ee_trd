"""Compute value-based price (VBP) curves for nominated focal strategies."""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis_core.io import load_analysis_inputs, assert_strategy_presence
from analysis_core.plotting import (
    add_horizontal_reference,
    figure_context,
    save_multiformat,
)
from analysis_v2.publication import write_caption_file, write_vbp_table, vbp_caption, display_name
from utils import set_seed

DEFAULT_STRATEGIES_YAML = PROJECT_ROOT / "config" / "strategies.yml"
DEFAULT_FOCALS = "Therapy A,Therapy B,Therapy C,Oral ketamine"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute VBP curves from PSA draws")
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
    parser.add_argument(
        "--focals",
        default=DEFAULT_FOCALS,
        help="Comma-separated list of focal strategies to analyse",
    )
    parser.add_argument("--lambda-min", dest="lambda_min", type=float, required=True)
    parser.add_argument("--lambda-max", dest="lambda_max", type=float, required=True)
    parser.add_argument("--lambda-step", dest="lambda_step", type=float, required=True)
    parser.add_argument(
        "--outdir",
        type=Path,
        required=True,
        help="Directory to store VBP outputs",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
        help="Random seed for reproducibility (default: 12345)",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Helpers
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


def parse_focals(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower())
    return slug.strip("_") or "strategy"


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


@dataclass
class VBPComponents:
    lambda_grid: np.ndarray
    p_star: np.ndarray
    expected_effect: float
    expected_k: float
    competitor_best_nmb: np.ndarray
    current_price: float


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------


def compute_vbp_components(
    lambda_grid: np.ndarray,
    focal: str,
    strategies: List[str],
    expected_cost: pd.Series,
    expected_effect: pd.Series,
    config_prices: dict,
) -> VBPComponents:
    if focal not in expected_cost.index:
        raise ValueError(f"Focal strategy '{focal}' not found in PSA data")
    if focal not in config_prices:
        raise KeyError(f"Price for focal strategy '{focal}' missing from strategies YAML")

    price = float(config_prices[focal])
    effect_i = float(expected_effect[focal])
    cost_i = float(expected_cost[focal])
    expected_k = cost_i - price

    effect_matrix = expected_effect[strategies].to_numpy()[None, :]
    cost_matrix = expected_cost[strategies].to_numpy()[None, :]
    lambda_column = lambda_grid[:, None]
    expected_nmb = lambda_column * effect_matrix - cost_matrix
    expected_nmb_df = pd.DataFrame(expected_nmb, columns=strategies, index=lambda_grid)

    if len(strategies) < 2:
        raise ValueError("At least two strategies are required to compute VBP curves")
    competitor_best = expected_nmb_df.drop(columns=[focal]).max(axis=1)

    p_star = lambda_grid * effect_i - expected_k - competitor_best.to_numpy()

    return VBPComponents(
        lambda_grid=lambda_grid,
        p_star=p_star,
        expected_effect=effect_i,
        expected_k=expected_k,
        competitor_best_nmb=competitor_best.to_numpy(),
        current_price=price,
    )


# ---------------------------------------------------------------------------
# Plotting & export
# ---------------------------------------------------------------------------


def plot_vbp_curve(components: VBPComponents, focal: str, perspective: str, outdir: Path, focal_label: str | None = None) -> None:
    ensure_output_dir(outdir)
    formatted_perspective = perspective.replace("_", " ").title()
    title_focal = focal_label or focal
    with figure_context(
        title=f"Value-Based Pricing Analysis – {title_focal} ({formatted_perspective})",
        xlabel="Willingness-to-Pay Threshold ($/QALY)",
        ylabel="Value-Based Price ($/Treatment)",
        figsize=(10, 6)
    ) as (fig, ax):
        # Enhanced VBP curve
        ax.plot(
            components.lambda_grid,
            components.p_star,
            label=f"Value-Based Price p*(λ) – {title_focal}",
            linewidth=3.0,
            color="#1f77b4",
            alpha=0.8
        )
        
        # Enhanced current price reference
        add_horizontal_reference(
            ax,
            components.current_price,
            label=f"Current Market Price – ${components.current_price:,.0f}",
            color="#d62728",
            linestyle="--",
            linewidth=2.5
        )
        
        # Add value zone shading
        ax.fill_between(components.lambda_grid, 
                       components.p_star, 
                       components.current_price,
                       where=(components.p_star > components.current_price),
                       alpha=0.2, color='green', 
                       label='Value Creation Zone')
        
        ax.fill_between(components.lambda_grid, 
                       components.p_star, 
                       components.current_price,
                       where=(components.p_star < components.current_price),
                       alpha=0.2, color='red', 
                       label='Value Destruction Zone')
        
        # Format axes
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Grid and styling
        ax.grid(True, alpha=0.3)
        ax.set_xlim(components.lambda_grid[0], components.lambda_grid[-1])
        
        # Enhanced legend
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, 
                 fancybox=True, shadow=True, fontsize=10)
        
        fig.tight_layout()
        focal_slug = focal.replace('-', '_').replace(' ', '_').lower()
        filename = f"v2_vbp_individual_{focal_slug}_{perspective.lower()}"
        save_multiformat(fig, outdir, filename, formats=['png', 'pdf', 'svg'], dpi=300)


def vbp_dataframe(components: VBPComponents, focal: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "lambda": components.lambda_grid,
            "strategy": focal,
            "p_star": components.p_star,
            "E_Ei": np.full_like(components.lambda_grid, components.expected_effect, dtype=float),
            "E_Ki": np.full_like(components.lambda_grid, components.expected_k, dtype=float),
            "expected_nmb_best_excl_focal": components.competitor_best_nmb,
        }
    )


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    set_seed(args.seed)

    lambda_grid = build_lambda_grid(args.lambda_min, args.lambda_max, args.lambda_step)

    data = load_analysis_inputs(
        psa_path=args.psa,
        config_path=args.strategies_yaml,
        perspective=args.perspective,
        lambda_grid=lambda_grid,
    )

    focals = parse_focals(args.focals)
    if not focals:
        raise ValueError("At least one focal strategy must be specified via --focals")

    # Check for focal strategies presence
    present_strategies, missing_strategies = assert_strategy_presence(
        data.table, args.perspective, focals
    )
    if not present_strategies:
        args.outdir.mkdir(parents=True, exist_ok=True)
        skip_note = f"VBP analysis skipped: no focal strategies found in PSA data for {args.perspective} perspective. Missing: {', '.join(missing_strategies)}"
        (args.outdir / "SKIP").write_text(skip_note)
        print(skip_note)
        return

    strategies = [s for s in data.config.strategies if s in data.table["strategy"].unique()]
    # Append any remaining strategies from PSA data to avoid dropping new additions.
    for strategy in data.table["strategy"].unique():
        if strategy not in strategies:
            strategies.append(strategy)

    cost_table = data.table.pivot(index="draw", columns="strategy", values="cost")[strategies]
    effect_table = data.table.pivot(index="draw", columns="strategy", values="effect")[strategies]

    expected_cost = cost_table.mean(axis=0)
    expected_effect = effect_table.mean(axis=0)

    aggregated_tables: List[pd.DataFrame] = []

    for focal in focals:
        if focal not in present_strategies:
            print(f"Warning: focal strategy '{focal}' not found in PSA data; skipping.")
            continue

        components = compute_vbp_components(
            lambda_grid=lambda_grid,
            focal=focal,
            strategies=strategies,
            expected_cost=expected_cost,
            expected_effect=expected_effect,
            config_prices=data.config.prices,
        )

        focal_slug = slugify(focal)
        focal_dir = args.outdir / focal_slug
        focal_label = display_name(focal, data.config)

        ensure_output_dir(focal_dir)
        focal_df = vbp_dataframe(components, focal)
        focal_df["display_strategy"] = focal_label
        focal_df.to_csv(focal_dir / "vbp_curve.csv", index=False)
        plot_vbp_curve(components, focal, args.perspective, focal_dir, focal_label=focal_label)
        caption_text = vbp_caption(
            perspective=args.perspective,
            config=data.config,
            lambda_values=lambda_grid,
            strategy=focal,
            current_price=components.current_price,
        )
        write_caption_file(focal_dir, "Figure_VBP.caption.md", caption_text)

        aggregated_tables.append(focal_df)
        print(f"VBP curve exported for '{focal}' to {focal_dir}")

    if aggregated_tables:
        aggregate = pd.concat(aggregated_tables, ignore_index=True)
        write_vbp_table(
            aggregate,
            outdir=args.outdir,
            perspective=args.perspective,
            config=data.config,
        )


if __name__ == "__main__":
    main()
