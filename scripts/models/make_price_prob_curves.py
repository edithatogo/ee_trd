"""Generate price–probability curves against a base strategy using PSA draws.

The script takes probabilistic sensitivity analysis (PSA) outputs and
computes, for each focal therapy, the probability of beating the base strategy
as a function of alternative prices. Two curves are produced per therapy:

* Expected-NMB (value-based price): price adjustment that drives expected
  incremental net monetary benefit (NMB) to zero.
* Probability-based curve: share of PSA draws in which the therapy dominates
  the base strategy at a given price point.

Results are written to CSV and plotted (PNG + SVG).
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "strategies.yml"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Price–probability curves from PSA data")
    parser.add_argument("--psa", type=Path, required=True, help="Path to PSA CSV file")
    parser.add_argument(
        "--base",
        default=None,
        help="Name of the base strategy (defaults to config value)",
    )
    parser.add_argument(
        "--focals",
        default=None,
        help="Comma-separated list of focal strategies; defaults to config strategies excluding the base",
    )
    parser.add_argument(
        "--lambda",
        dest="wtp",
        type=float,
        required=True,
        help="Willingness-to-pay (per unit of effect)",
    )
    parser.add_argument(
        "--prices-current",
        default="",
        help="Comma-separated mapping of strategy:price entries to override config prices",
    )
    parser.add_argument("--price-min", type=float, required=True)
    parser.add_argument("--price-max", type=float, required=True)
    parser.add_argument("--price-step", type=float, required=True)
    parser.add_argument(
        "--perspective",
        required=True,
        help="Perspective label (e.g. health_system, societal)",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        required=True,
        help="Directory to store CSV/figure outputs",
    )
    parser.add_argument(
        "--effect-column",
        default=None,
        help="Optional column name to treat as effect (default auto-detect)",
    )
    parser.add_argument(
        "--cost-column",
        default=None,
        help="Optional column name to treat as cost (default 'cost')",
    )
    parser.add_argument(
        "--draw-column",
        default=None,
        help="Optional column name to treat as draw/iteration id (default auto-detect)",
    )
    parser.add_argument(
        "--perspective-column",
        default=None,
        help="Optional column containing perspective labels to filter on",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to strategy configuration YAML",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Data loading & validation
# ---------------------------------------------------------------------------


def load_strategy_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Strategy config not found at '{path}'")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    required_keys = {"base", "perspectives", "strategies", "prices"}
    missing = required_keys - set(data)
    if missing:
        raise KeyError(
            "Strategy config missing required keys: " + ", ".join(sorted(missing))
        )

    data["perspectives"] = list(data.get("perspectives", []))
    data["strategies"] = list(data.get("strategies", []))
    if not data["strategies"]:
        raise ValueError("Strategy config must list at least one strategy")

    prices = data.get("prices", {})
    data["prices"] = {str(k): float(v) for k, v in prices.items()}
    return data


def parse_mapping(mapping: str) -> Dict[str, float]:
    result: Dict[str, float] = {}
    if not mapping.strip():
        return result
    for item in mapping.split(","):
        if ":" not in item:
            raise ValueError(f"Invalid price mapping entry '{item}'")
        key, value = item.split(":", 1)
        key = key.strip()
        try:
            result[key] = float(value)
        except ValueError as exc:
            raise ValueError(f"Invalid price value in mapping '{item}'") from exc
    return result


def normalise_perspective(requested: str, available: List[str]) -> str:
    if requested in available:
        return requested
    lookup = {p.lower().replace("_", ""): p for p in available}
    key = requested.lower().replace("_", "")
    if key in lookup:
        return lookup[key]
    raise ValueError(
        f"Perspective '{requested}' not present in config. Available: {available}"
    )


def standardise_columns(df: pd.DataFrame, draw_col: str | None, cost_col: str | None, effect_col: str | None) -> pd.DataFrame:
    df = df.copy()

    # Strategy column
    if "strategy" not in df.columns:
        raise KeyError("PSA file must contain a 'strategy' column")

    # Draw column
    if draw_col is None:
        for candidate in ("draw", "iter", "iteration", "sample"):
            if candidate in df.columns:
                draw_col = candidate
                break
    if draw_col is None:
        raise KeyError("Unable to determine draw column; specify --draw-column")
    df = df.rename(columns={draw_col: "draw"})

    # Cost column
    if cost_col is None:
        cost_col = "cost" if "cost" in df.columns else None
    if cost_col is None or cost_col not in df.columns:
        raise KeyError("Unable to determine cost column; specify --cost-column")
    df = df.rename(columns={cost_col: "cost"})

    # Effect column
    if effect_col is None:
        for candidate in ("effect", "qalys", "qaly", "utility"):
            if candidate in df.columns:
                effect_col = candidate
                break
    if effect_col is None or effect_col not in df.columns:
        raise KeyError("Unable to determine effect column; specify --effect-column")
    df = df.rename(columns={effect_col: "effect"})

    required = {"draw", "strategy", "cost", "effect"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required columns: {', '.join(sorted(missing))}")

    # Ensure numeric
    for col in ("draw", "cost", "effect"):
        if not np.issubdtype(df[col].dtype, np.number):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if not np.isfinite(df[["draw", "cost", "effect"]].to_numpy()).all():
        raise ValueError("PSA file contains non-finite draw/cost/effect values")

    return df


def filter_perspective(df: pd.DataFrame, perspective: str, perspective_col: str | None) -> pd.DataFrame:
    if perspective_col is None:
        return df
    if perspective_col not in df.columns:
        raise KeyError(f"Perspective column '{perspective_col}' not found in PSA file")
    subset = df[df[perspective_col] == perspective]
    if subset.empty:
        raise ValueError(f"No rows found for perspective '{perspective}'")
    return subset


def prepare_wide(df: pd.DataFrame, strategies: List[str]) -> pd.DataFrame:
    pivot_cost = df.pivot_table(index="draw", columns="strategy", values="cost", aggfunc="first")
    pivot_effect = df.pivot_table(index="draw", columns="strategy", values="effect", aggfunc="first")

    for strategy in strategies:
        if strategy not in pivot_cost.columns:
            raise ValueError(f"Strategy '{strategy}' not found in PSA data")

    # Align draws and ensure no missing
    merged_cost = pivot_cost[strategies]
    merged_effect = pivot_effect[strategies]
    if merged_cost.isna().any().any() or merged_effect.isna().any().any():
        raise ValueError("Missing cost/effect values after pivot; ensure draw IDs align across strategies")

    wide = pd.concat({"cost": merged_cost, "effect": merged_effect}, axis=1)
    wide.sort_index(inplace=True)
    return wide


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------


def price_grid(price_min: float, price_max: float, price_step: float) -> np.ndarray:
    if price_step <= 0:
        raise ValueError("price_step must be positive")
    n_steps = int(math.floor((price_max - price_min) / price_step + 0.5))
    grid = price_min + price_step * np.arange(n_steps + 1)
    if grid[-1] < price_max:
        grid = np.append(grid, price_max)
    return grid


def compute_probability_curve(delta_effect: np.ndarray, delta_k: np.ndarray, price_grid: np.ndarray, wtp: float) -> np.ndarray:
    prob = []
    for price in price_grid:
        nmb = wtp * delta_effect - (delta_k + price)
        prob.append(float(np.mean(nmb > 0)))
    return np.array(prob)


def expected_nmb_threshold(delta_effect: np.ndarray, delta_k: np.ndarray, wtp: float) -> float:
    exp_delta_e = delta_effect.mean()
    exp_delta_k = delta_k.mean()
    return wtp * exp_delta_e - exp_delta_k


def crossing_price(prices: np.ndarray, probabilities: np.ndarray, target: float = 0.5) -> float | None:
    above = probabilities >= target
    if not np.any(above):
        return None
    if np.all(above):
        return float(prices[-1])

    idx = np.where(above)[0][-1]
    if idx == len(prices) - 1:
        return float(prices[idx])
    p1, p2 = prices[idx], prices[idx + 1]
    v1, v2 = probabilities[idx], probabilities[idx + 1]
    if v1 == v2:
        return float(p1)
    interpolated = p1 + (target - v1) * (p2 - p1) / (v2 - v1)
    return float(interpolated)


# ---------------------------------------------------------------------------
# Plotting & export
# ---------------------------------------------------------------------------


def plot_curves(
    outdir: Path,
    perspective: str,
    price_grid: np.ndarray,
    curves: Dict[str, np.ndarray],
    current_prices: Dict[str, float],
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)

    colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["#1f77b4", "#ff7f0e", "#2ca02c"])
    color_map = {name: colors[i % len(colors)] for i, name in enumerate(curves.keys())}

    for therapy, probs in curves.items():
        ax.plot(price_grid, probs, label=therapy, linewidth=2.0, color=color_map[therapy])
        current_price = current_prices.get(therapy)
        if current_price is not None:
            ax.axvline(
                current_price,
                color=color_map[therapy],
                linestyle=":",
                linewidth=1.5,
                alpha=0.8,
            )

    ax.set_xlabel("Price (per patient)")
    ax.set_ylabel("Probability beats base strategy")
    ax.set_ylim(0, 1)
    ax.set_title(f"Price–probability curves ({perspective})")
    ax.legend(frameon=False)

    fig.tight_layout()
    png_path = outdir / f"price_prob_{perspective}.png"
    svg_path = outdir / f"price_prob_{perspective}.svg"
    fig.savefig(png_path, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)


def export_csv(outdir: Path, perspective: str, price_grid: np.ndarray, curves: Dict[str, np.ndarray]) -> Path:
    rows = []
    for therapy, probs in curves.items():
        for price, prob in zip(price_grid, probs):
            rows.append({"therapy": therapy, "price": price, "prob_beats_base": prob})
    df = pd.DataFrame(rows)
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"price_prob_{perspective}.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)

    config = load_strategy_config(args.config)
    config_perspective = normalise_perspective(args.perspective, config["perspectives"])

    psa = pd.read_csv(args.psa)
    psa = standardise_columns(psa, args.draw_column, args.cost_column, args.effect_column)
    try:
        psa = filter_perspective(psa, args.perspective, args.perspective_column)
    except ValueError:
        if config_perspective != args.perspective:
            psa = filter_perspective(psa, config_perspective, args.perspective_column)
        else:
            raise

    available_strategies = [
        strategy for strategy in config["strategies"] if strategy in psa["strategy"].unique()
    ]
    if not available_strategies:
        raise ValueError(
            "No overlapping strategies between config and PSA for the selected perspective"
        )

    base_strategy = args.base or config["base"]
    if base_strategy not in available_strategies:
        raise ValueError(
            f"Base strategy '{base_strategy}' not present in both config and PSA. "
            f"Available: {available_strategies}"
        )

    if args.focals:
        requested = [s.strip() for s in args.focals.split(",") if s.strip()]
    else:
        requested = [s for s in config["strategies"] if s != base_strategy]

    missing_requested = [s for s in requested if s not in available_strategies]
    if missing_requested:
        print(
            "Warning: dropping focal strategies absent from PSA/config intersection: "
            + ", ".join(missing_requested)
        )

    focal_strategies = [
        s for s in requested if s in available_strategies and s != base_strategy
    ]
    if not focal_strategies:
        raise ValueError("At least one focal strategy must remain after filtering")

    price_map = {**config.get("prices", {}), **parse_mapping(args.prices_current)}
    missing_prices = [s for s in focal_strategies if s not in price_map]
    if missing_prices:
        raise ValueError(
            "Missing price entries for strategies: " + ", ".join(missing_prices)
        )

    selected_strategies = [base_strategy] + focal_strategies
    psa = psa[psa["strategy"].isin(selected_strategies)].copy()

    wide = prepare_wide(psa, selected_strategies)
    cost = wide["cost"].to_numpy()
    effect = wide["effect"].to_numpy()

    base_cost = cost[:, 0]
    base_effect = effect[:, 0]

    price_grid_values = price_grid(args.price_min, args.price_max, args.price_step)

    curves: Dict[str, np.ndarray] = {}
    notes: List[str] = []

    for idx, therapy in enumerate(focal_strategies, start=1):
        current_price = price_map[therapy]
        delta_effect = effect[:, idx] - base_effect
        k = cost[:, idx] - current_price
        delta_k = k - base_cost

        prob_curve = compute_probability_curve(delta_effect, delta_k, price_grid_values, args.wtp)
        curves[therapy] = prob_curve

        vbp_threshold = expected_nmb_threshold(delta_effect, delta_k, args.wtp)
        cross = crossing_price(price_grid_values, prob_curve, target=0.5)

        if cross is None:
            interpretation = (
                f"{therapy}: probability < 0.5 across price range; "
                f"value-based price = {vbp_threshold:,.0f}."
            )
        else:
            interpretation = (
                f"{therapy}: reaches 50% probability at price ≈ {cross:,.0f}; "
                f"value-based price = {vbp_threshold:,.0f}; "
                f"current price = {current_price:,.0f}."
            )
        notes.append(interpretation)

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    csv_path = export_csv(outdir, config_perspective, price_grid_values, curves)
    plot_curves(outdir, config_perspective, price_grid_values, curves, price_map)

    print(f"Saved price probability curves to {csv_path}")
    for note in notes:
        print(note)


if __name__ == "__main__":
    main()