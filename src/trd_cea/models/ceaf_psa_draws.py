"""Construct a cost-effectiveness acceptability frontier (CEAF) from PSA draws."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_ROOT / "results"

STRATEGIES: Tuple[str, ...] = ("Ketamine", "Esketamine", "Psilocybin")
PALETTE = {
    "Ketamine": "#023047",
    "Esketamine": "#219EBC",
    "Psilocybin": "#FFB703",
}


@dataclass(frozen=True)
class FrontierPoint:
    wtp: float
    strategy: str
    probability: float


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

    required = {"iter", "strategy", "incremental_cost", "incremental_qalys"}
    missing = required - set(psa.columns)
    if missing:
        raise KeyError(
            "PSA results are missing required columns: " + ", ".join(sorted(missing))
        )

    psa = psa[psa["strategy"].isin(STRATEGIES)].copy()
    psa = psa.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["incremental_cost", "incremental_qalys"]
    )
    return psa


def build_arrays(psa: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    pivot_cost = psa.pivot_table(
        index="iter", columns="strategy", values="incremental_cost", aggfunc="first"
    )
    pivot_qaly = psa.pivot_table(
        index="iter", columns="strategy", values="incremental_qalys", aggfunc="first"
    )

    missing_cols = [s for s in STRATEGIES if s not in pivot_cost.columns]
    if missing_cols:
        raise ValueError(
            "PSA results are missing strategies: " + ", ".join(missing_cols)
        )

    inc_cost = pivot_cost.loc[:, STRATEGIES].to_numpy()
    inc_qaly = pivot_qaly.loc[:, STRATEGIES].to_numpy()
    return inc_cost, inc_qaly


def wtp_grid(country: str) -> np.ndarray:
    if country.upper() == "AU":
        return np.linspace(0, 100_000, 201)
    return np.linspace(0, 60_000, 181)


def compute_frontier(
    inc_cost: np.ndarray, inc_qaly: np.ndarray, wtp_values: np.ndarray
) -> List[FrontierPoint]:
    frontier: List[FrontierPoint] = []
    for wtp in wtp_values:
        net_benefit = wtp * inc_qaly - inc_cost  # shape: draws x strategies
        expected_nb = net_benefit.mean(axis=0)
        best_idx = int(np.argmax(expected_nb))
        best_strategy = STRATEGIES[best_idx]

        max_per_draw = net_benefit.max(axis=1)
        probability = float(np.mean(net_benefit[:, best_idx] >= max_per_draw - 1e-9))
        frontier.append(FrontierPoint(wtp=wtp, strategy=best_strategy, probability=probability))
    return frontier


def plot_frontier(
    frontier: List[FrontierPoint], country: str, perspective: str, output: Path
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    wtp_vals = np.array([pt.wtp for pt in frontier])
    probs = np.array([pt.probability for pt in frontier])
    strategies = [pt.strategy for pt in frontier]

    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    ax.plot(wtp_vals, probs, color="#212529", linewidth=2.0)

    # Shade regions where the optimal strategy changes
    start = wtp_vals[0]
    current = strategies[0]
    for i in range(1, len(frontier)):
        if strategies[i] != current:
            ax.axvspan(
                start,
                wtp_vals[i - 1],
                color=PALETTE.get(current, "#dee2e6"),
                alpha=0.12,
            )
            start = wtp_vals[i]
            current = strategies[i]
    ax.axvspan(
        start,
        wtp_vals[-1],
        color=PALETTE.get(current, "#dee2e6"),
        alpha=0.12,
    )

    currency = "AUD" if country.upper() == "AU" else "NZD"
    ax.set_xlabel(f"WTP ({currency} per QALY)")
    ax.set_ylabel("Probability optimal strategy is cost-effective")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.2)
    ax.set_title(
        "Cost-effectiveness acceptability frontier\n"
        f"{country.upper()} – {perspective.capitalize()} perspective"
    )

    # Strategy legend based on shaded colours
    handles = []
    labels = []
    for strategy in STRATEGIES:
        handles.append(plt.Line2D([0], [0], color=PALETTE.get(strategy, "#6c757d"), lw=6))
        labels.append(strategy)
    ax.legend(handles, labels, frameon=False, title="Optimal strategy (by colour)")

    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CEAF from PSA results")
    parser.add_argument("--country", choices=["AU", "NZ"], required=True)
    parser.add_argument("--perspective", choices=["healthcare", "societal"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    psa = load_psa(args.country, args.perspective)
    inc_cost, inc_qaly = build_arrays(psa)
    frontier = compute_frontier(inc_cost, inc_qaly, wtp_grid(args.country))
    plot_frontier(frontier, args.country, args.perspective, args.output)


if __name__ == "__main__":
    main()
