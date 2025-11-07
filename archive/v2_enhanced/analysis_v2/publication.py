"""Utilities for assembling publication-ready tables, captions, and methods text."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from analysis_core.export import (
    build_ceaf_table,
    build_probability_threshold_table,
    build_vbp_table,
    write_table,
)
from analysis_core.io import StrategyConfig


def display_name(name: str, config: StrategyConfig) -> str:
    """Return a human-friendly display name for a strategy.

    Falls back to the raw name if not mapped in config.labels.
    """
    return config.labels.get(name, name)
from analysis_core.plotting import write_caption


@dataclass(frozen=True)
class GridSummary:
    minimum: float
    maximum: float
    step: float | None

    def describe(self, symbol: str) -> str:
        if self.step is None:
            return f"{symbol} = {self.minimum:,.0f}"
        return f"{symbol} ∈ [{self.minimum:,.0f}, {self.maximum:,.0f}] in increments of {self.step:,.0f}"


def _analysis_root(outdir: Path) -> Path:
    try:
        return outdir.parents[1]
    except IndexError:
        return outdir.parent


def tables_dir(base_outdir: Path, perspective: str) -> Path:
    root = _analysis_root(base_outdir)
    target = root / "tables_for_manuscript" / perspective
    target.mkdir(parents=True, exist_ok=True)
    return target


def grid_summary(values: Sequence[float]) -> GridSummary:
    arr = np.asarray(values, dtype=float)
    arr = np.unique(arr)
    arr.sort()
    if arr.size == 1:
        return GridSummary(minimum=float(arr[0]), maximum=float(arr[0]), step=None)
    diffs = np.diff(arr)
    step = float(np.min(diffs)) if np.allclose(diffs, diffs[0]) else float(diffs[0])
    return GridSummary(minimum=float(arr[0]), maximum=float(arr[-1]), step=step)


def write_ceaf_table(
    probabilities_df: pd.DataFrame,
    ceaf_df: pd.DataFrame,
    outdir: Path,
    perspective: str,
    config: StrategyConfig,
    lambda_values: Sequence[float],
) -> Path:
    metadata = {
        "perspective": perspective,
        "base_strategy": config.base,
        "currency": config.currency,
        "lambda_min": float(np.min(lambda_values)),
        "lambda_max": float(np.max(lambda_values)),
    }
    summary = build_ceaf_table(probabilities_df, ceaf_df, metadata=metadata)
    if "strategy" in summary.columns:
        summary["display_strategy"] = summary["strategy"].map(lambda s: display_name(str(s), config))
    tables_path = tables_dir(outdir, perspective) / f"ceaf_{perspective}.csv"
    return write_table(summary, tables_path.parent, tables_path.name)


def write_vbp_table(
    vbp_df: pd.DataFrame,
    outdir: Path,
    perspective: str,
    config: StrategyConfig,
) -> Path:
    metadata = {
        "perspective": perspective,
        "base_strategy": config.base,
        "currency": config.currency,
    }
    table = build_vbp_table(vbp_df, metadata=metadata)
    # Ensure display label is present
    if "display_strategy" not in table.columns and "strategy" in table.columns:
        table["display_strategy"] = table["strategy"].map(lambda s: display_name(str(s), config))
    tables_path = tables_dir(outdir, perspective) / f"vbp_{perspective}.csv"
    return write_table(table, tables_path.parent, tables_path.name)


def write_price_threshold_table(
    probabilities_df: pd.DataFrame,
    outdir: Path,
    perspective: str,
    config: StrategyConfig,
    lambda_value: float,
    threshold: float = 0.5,
) -> Path:
    metadata = {
        "perspective": perspective,
        "base_strategy": config.base,
        "currency": config.currency,
        "lambda_value": lambda_value,
    }
    table = build_probability_threshold_table(
        probabilities_df,
        group_col="therapy",
        price_col="price",
        prob_col="prob_beats_base",
        threshold=threshold,
        metadata=metadata,
    )
    if "therapy" in table.columns:
        table["display_therapy"] = table["therapy"].map(lambda s: display_name(str(s), config))
    tables_path = tables_dir(outdir, perspective) / f"price_threshold_{perspective}.csv"
    return write_table(table, tables_path.parent, tables_path.name)


def ceaf_caption(
    perspective: str,
    config: StrategyConfig,
    lambda_values: Sequence[float],
) -> str:
    grid = grid_summary(lambda_values)
    _perspective_label = perspective.replace("_", " ").title()
    # Add horizon and discount information (based on settings.yaml)
    horizon_years = 10
    discount_cost = "5% (AU) / 3.5% (NZ)"
    discount_qaly = "5% (AU) / 3.5% (NZ)"
    base_comparator = display_name(config.base, config)

    return (
        f"**Figure:** Cost-effectiveness acceptability frontier for the {perspective_label} perspective over a {horizon_years}-year time horizon. "
        f"Curves show the probability each strategy is optimal given {grid.describe('λ')} in {config.currency} per {config.effects_unit}. "
        f"Analysis uses {discount_cost} annual discount rate for costs and {discount_qaly} for QALYs. "
        f"The CEAF traces the probability that the strategy with the highest expected net monetary benefit (NMB) beats the base comparator ({base_comparator})."
    )


def vbp_caption(
    perspective: str,
    config: StrategyConfig,
    lambda_values: Sequence[float],
    strategy: str | None = None,
    current_price: float | None = None,
) -> str:
    grid = grid_summary(lambda_values)
    _perspective_label = perspective.replace("_", " ").title()
    # Add horizon and discount information (based on settings.yaml)
    horizon_years = 10
    discount_cost = "5% (AU) / 3.5% (NZ)"
    discount_qaly = "5% (AU) / 3.5% (NZ)"
    base_comparator = display_name(config.base, config)

    if strategy:
        focal_text = f" focusing on {display_name(strategy, config)}"
    else:
        focal_text = ""
    if current_price is not None:
        price_text = (
            f" Horizontal dashed lines mark the current list price of {current_price:,.0f} {config.currency}."
        )
    else:
        price_text = " Horizontal dashed lines indicate current list prices from the strategy configuration."
    return (
        f"**Figure:** Value-based price thresholds{focal_text} for the {perspective_label} perspective over a {horizon_years}-year time horizon. "
        f"Each curve shows p*(λ)=λ·E[E_i]−E[K_i]−\\max_j E[NMB_j(λ)] for a therapy relative to base comparator {base_comparator}. "
        f"Analysis uses {discount_cost} annual discount rate for costs and {discount_qaly} for QALYs. "
        f"Analyses use {grid.describe('λ')} with costs in {config.currency} and effects measured in {config.effects_unit}."
        f"{price_text}"
    )


def price_probability_caption(
    perspective: str,
    config: StrategyConfig,
    lambda_value: float,
    price_values: Sequence[float],
) -> str:
    grid = grid_summary(price_values)
    _perspective_label = perspective.replace("_", " ").title()
    # Add horizon and discount information (based on settings.yaml)
    horizon_years = 10
    discount_cost = "5% (AU) / 3.5% (NZ)"
    discount_qaly = "5% (AU) / 3.5% (NZ)"
    base_label = display_name(config.base, config)

    return (
        f"**Figure:** Probability each therapy is cost-effective versus {base_label} across price points in the {perspective_label} perspective over a {horizon_years}-year time horizon. "
        f"Probabilities represent Pr(NMB_i(λ,p) > NMB_{base_label}(λ)) with λ={lambda_value:,.0f} {config.currency}/{config.effects_unit}. "
        f"Analysis uses {discount_cost} annual discount rate for costs and {discount_qaly} for QALYs. "
        f"Prices evaluated over {grid.describe('p')} with vertical lines marking current prices."
    )


def write_caption_file(outdir: Path, filename: str, text: str) -> Path:
    return write_caption(outdir, filename, text)


def write_methods_snippet(
    outdir: Path,
    config: StrategyConfig,
    perspectives: Iterable[str],
    lambda_min: float,
    lambda_max: float,
    lambda_step: float,
    lambda_single: float,
    price_min: float,
    price_max: float,
    price_step: float,
    psa_path: Path,
    strategies_path: Path,
    seed: int,
) -> Path:
    root = _analysis_root(outdir)
    snippet_path = root / "methods_snippet.md"
    _perspective_label = ", ".join(p.replace("_", " ") for p in perspectives)
    text = """## Probabilistic methods\n\n"""
    text += (
        f"Probabilistic sensitivity analysis (PSA) draws were taken from `{psa_path.name}` "
        f"using the strategy definitions provided in `{strategies_path.name}`. "
        f"Each draw produced costs (in {config.currency}) and effects (in {config.effects_unit}), "
        "which were combined into net monetary benefit (NMB) as NMB = λ·E − C. Expected NMB values "
        "were calculated for each strategy under the {perspective_label} perspectives.\n\n"
    )
    text += (
        f"The cost-effectiveness acceptability frontier (CEAF) identifies the strategy with the highest expected NMB across λ ∈ [{lambda_min:,.0f}, {lambda_max:,.0f}] in {lambda_step:,.0f} increments. "
        "Value-based pricing thresholds were derived by solving p*(λ)=λ·E[E_i]−E[K_i]−max_j E[NMB_j(λ)] for each therapy relative to the base comparator. "
        f"Price–probability curves evaluate Pr(NMB_i(λ,p) > NMB_{config.base}(λ)) across prices p ∈ [{price_min:,.0f}, {price_max:,.0f}] in {price_step:,.0f} increments at λ={lambda_single:,.0f}. "
        f"All analyses were seeded with {seed} to support reproducibility.\n"
    )
    snippet_path.write_text(text, encoding="utf-8")
    return snippet_path
