"""Generate value-based and probability-based threshold price curves from PSA draws.

Value-based price (VBP) curve: price adjustment that sets expected incremental
net monetary benefit (NMB) to zero for the selected strategy.

Probability-based curve: maximum price adjustment that keeps the strategy as the
most likely to be cost-effective (highest probability of yielding the greatest
net benefit among comparators).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "strategies.yml"


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

    return data


def perspective_variants(perspective: str) -> List[str]:
    variants: List[str] = [perspective]
    compact = perspective.replace("_", "")
    if compact not in variants:
        variants.append(compact)
    if perspective == "health_system" and "healthcare" not in variants:
        variants.append("healthcare")
    elif perspective == "healthcare" and "health_system" not in variants:
        variants.append("health_system")
    return variants


def psa_candidate_paths(country: str, perspective: str) -> Iterable[Path]:
    variants = perspective_variants(perspective)
    filenames = [f"psa_results_{country}_{variant}.csv" for variant in variants]
    filenames.append(f"psa_results_{country}.csv")
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

    required = {"iter", "strategy", "incremental_cost", "incremental_qalys"}
    missing = required - set(psa.columns)
    if missing:
        raise KeyError(
            "PSA results are missing required columns: " + ", ".join(sorted(missing))
        )

    psa = psa.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["incremental_cost", "incremental_qalys"]
    )
    return psa


def pivot_arrays(psa: pd.DataFrame, strategies: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    cost = psa.pivot_table(
        index="iter", columns="strategy", values="incremental_cost", aggfunc="first"
    )
    qaly = psa.pivot_table(
        index="iter", columns="strategy", values="incremental_qalys", aggfunc="first"
    )

    missing_cols = [s for s in strategies if s not in cost.columns]
    if missing_cols:
        raise ValueError(
            "PSA results are missing required strategies: " + ", ".join(missing_cols)
        )

    cost_arr = cost.loc[:, strategies].to_numpy()
    qaly_arr = qaly.loc[:, strategies].to_numpy()
    return cost_arr, qaly_arr


def wtp_grid(country: str) -> np.ndarray:
    return np.linspace(0, 100_000, 201) if country.upper() == "AU" else np.linspace(0, 60_000, 181)


def value_based_price(expected_cost: float, expected_qaly: float, wtp: float) -> float:
    """Return incremental price adjustment that sets expected incremental NMB to zero."""
    return wtp * expected_qaly - expected_cost


def compute_vbp_curve(
    inc_cost: np.ndarray, inc_qaly: np.ndarray, strategy_index: int, wtp_values: np.ndarray
) -> np.ndarray:
    mean_cost = inc_cost[:, strategy_index].mean()
    mean_qaly = inc_qaly[:, strategy_index].mean()
    return np.array([value_based_price(mean_cost, mean_qaly, w) for w in wtp_values])


def strategy_shares(
    price_adjust: float,
    nb_target: np.ndarray,
    nb_others: np.ndarray,
) -> Tuple[float, np.ndarray]:
    nb_target_adj = nb_target - price_adjust
    all_nb = np.column_stack([nb_target_adj, nb_others])
    best_idx = np.argmax(all_nb, axis=1)
    counts = np.bincount(best_idx, minlength=1 + nb_others.shape[1])
    shares = counts / counts.sum()
    return shares[0], shares[1:]


def probability_threshold(
    nb_matrix: np.ndarray,
    strategy_index: int,
    price_bounds: Tuple[float, float],
) -> float:
    target = nb_matrix[:, strategy_index]
    others = np.delete(nb_matrix, strategy_index, axis=1)

    low, high = price_bounds
    target_low, others_low = strategy_shares(low, target, others)
    if target_low < others_low.max():
        return np.nan

    target_high, others_high = strategy_shares(high, target, others)
    if target_high >= others_high.max():
        return float(high)

    for _ in range(50):
        mid = 0.5 * (low + high)
        target_mid, others_mid = strategy_shares(mid, target, others)
        if target_mid >= others_mid.max():
            low = mid
        else:
            high = mid
    return float(low)


def compute_probability_curve(
    inc_cost: np.ndarray,
    inc_qaly: np.ndarray,
    strategy_index: int,
    wtp_values: np.ndarray,
    price_bounds: Tuple[float, float] = (-100_000.0, 100_000.0),
) -> np.ndarray:
    curve = []
    for wtp in wtp_values:
        nb_matrix = wtp * inc_qaly - inc_cost
        threshold = probability_threshold(nb_matrix, strategy_index, price_bounds)
        curve.append(threshold)
    return np.array(curve)


def currency_label(country: str) -> str:
    return "AUD" if country.upper() == "AU" else "NZD"


def plot_curves(
    wtp_values: np.ndarray,
    vbp: np.ndarray,
    prob_curve: np.ndarray,
    strategy: str,
    country: str,
    perspective: str,
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    ax.plot(wtp_values, vbp, label="Expected-NMB threshold (VBP)", linewidth=2.0, color="#023047")
    ax.plot(
        wtp_values,
        prob_curve,
        label="Probability-optimal threshold",
        linewidth=2.0,
        color="#FB8500",
        linestyle="--",
    )

    currency = currency_label(country)
    ax.set_xlabel(f"WTP ({currency} per QALY)")
    ax.set_ylabel("Price adjustment (currency units per patient)")
    ax.grid(True, alpha=0.2)
    ax.legend(frameon=False)
    ax.set_title(
        "Threshold price curves\n"
        f"{strategy} – {country.upper()} {perspective.capitalize()} perspective"
    )

    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def save_csv(
    path: Path,
    wtp: np.ndarray,
    vbp: np.ndarray,
    prob_curve: np.ndarray,
) -> None:
    df = pd.DataFrame({"wtp": wtp, "vbp_price": vbp, "probability_threshold_price": prob_curve})
    df.to_csv(path, index=False)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate threshold price curves from PSA results")
    parser.add_argument("--country", choices=["AU", "NZ"], required=True)
    parser.add_argument("--perspective", required=True, help="Perspective name (must appear in config)")
    parser.add_argument("--strategy", required=True, help="Strategy to analyse (must appear in config & PSA)")
    parser.add_argument("--output", type=Path, required=True, help="Destination PNG file path")
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional CSV export of the threshold curves",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to strategy configuration YAML",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)

    config = load_strategy_config(args.config)
    if args.perspective not in config["perspectives"]:
        normalised = {p.lower().replace("_", ""): p for p in config["perspectives"]}
        key = args.perspective.lower().replace("_", "")
        if key not in normalised:
            raise ValueError(
                f"Perspective '{args.perspective}' not found in config. Available: {config['perspectives']}"
            )
        config_perspective = normalised[key]
    else:
        config_perspective = args.perspective

    psa = load_psa(args.country, args.perspective)
    available_strategies = [
        strategy for strategy in config["strategies"] if strategy in psa["strategy"].unique()
    ]
    if not available_strategies:
        raise ValueError(
            "No overlapping strategies between config and PSA results for the chosen perspective"
        )

    psa = psa[psa["strategy"].isin(available_strategies)].copy()

    if args.strategy not in available_strategies:
        raise ValueError(
            f"Strategy '{args.strategy}' unavailable; overlapping strategies: {available_strategies}"
        )

    inc_cost, inc_qaly = pivot_arrays(psa, available_strategies)
    strategy_index = available_strategies.index(args.strategy)

    wtp_values = wtp_grid(args.country)
    vbp_curve = compute_vbp_curve(inc_cost, inc_qaly, strategy_index, wtp_values)
    prob_curve = compute_probability_curve(inc_cost, inc_qaly, strategy_index, wtp_values)

    plot_curves(
        wtp_values,
        vbp_curve,
        prob_curve,
        args.strategy,
        args.country,
        config_perspective,
        args.output,
    )

    if args.output_csv is not None:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        save_csv(args.output_csv, wtp_values, vbp_curve, prob_curve)


if __name__ == "__main__":
    main()