"""Input/output utilities for PSA analyses.

Responsibilities:
- Load PSA CSVs and strategy configuration YAML.
- Validate schema integrity across perspectives and strategies.
- Align draw identifiers across strategies.
- Compute price-adjusted costs (K_i) where applicable.
- Ensure unit consistency between effects and willingness-to-pay (λ).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
import yaml


REQUIRED_PSA_COLUMNS = {"draw", "strategy", "cost", "effect", "perspective"}


@dataclass
class StrategyConfig:
    base: str
    perspectives: List[str]
    strategies: List[str]
    prices: Dict[str, float]
    effects_unit: str
    currency: str
    labels: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "StrategyConfig":
        if not path.exists():
            raise FileNotFoundError(f"Strategy configuration missing at '{path}'")
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        required = {"base", "perspectives", "strategies", "prices", "effects_unit", "currency"}
        missing = required - set(data)
        if missing:
            raise KeyError(f"Strategy config missing keys: {', '.join(sorted(missing))}")
        return cls(
            base=data["base"],
            perspectives=list(data["perspectives"]),
            strategies=list(data["strategies"]),
            prices={k: float(v) for k, v in data["prices"].items()},
            effects_unit=str(data["effects_unit"]),
            currency=str(data["currency"]),
            labels={str(k): str(v) for k, v in (data.get("labels") or {}).items()},
        )


@dataclass
class PSAData:
    table: pd.DataFrame
    config: StrategyConfig
    perspective: str

    @property
    def strategies(self) -> List[str]:
        return list(self.table["strategy"].unique())

    @property
    def draws(self) -> np.ndarray:
        return np.sort(self.table["draw"].unique())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalise_perspective(perspective: str, available: Iterable[str]) -> str:
    items = list(available)
    if perspective in items:
        return perspective
    lookup = {p.lower().replace("_", ""): p for p in items}
    key = perspective.lower().replace("_", "")
    if key in lookup:
        return lookup[key]
    raise ValueError(
        f"Perspective '{perspective}' not found. Available: {items}"
    )


def load_psa(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"PSA file not found at '{path}'")
    df = pd.read_csv(path)
    missing = REQUIRED_PSA_COLUMNS - set(df.columns)
    if missing:
        raise KeyError(
            "PSA file missing columns: " + ", ".join(sorted(missing))
        )
    df = df.replace([np.inf, -np.inf], np.nan)
    required_cols = list(REQUIRED_PSA_COLUMNS)
    if df[required_cols].isna().any().any():
        raise ValueError("PSA file contains NaNs in required columns")
    return df


def filter_perspective(df: pd.DataFrame, perspective: str) -> pd.DataFrame:
    subset = df[df["perspective"] == perspective].copy()
    if subset.empty:
        raise ValueError(
            f"No PSA draws for perspective '{perspective}'"
        )
    return subset


def ensure_strategy_overlap(df: pd.DataFrame, strategies: List[str]) -> pd.DataFrame:
    available = df["strategy"].unique()
    overlap = [s for s in strategies if s in available]
    if not overlap:
        raise ValueError("No overlapping strategies between PSA data and config")
    subset = df[df["strategy"].isin(overlap)].copy()
    return subset


def align_draws(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("strategy")
    reference = None
    for strategy, group in grouped:
        draws = np.sort(group["draw"].unique())
        if reference is None:
            reference = draws
        elif len(draws) != len(reference) or not np.array_equal(draws, reference):
            raise ValueError(
                "Draw IDs misaligned across strategies; ensure PSA input is balanced"
            )
    return df


def compute_price_adjusted_costs(df: pd.DataFrame, config: StrategyConfig, focal: Optional[str] = None) -> pd.DataFrame:
    result = df.copy()
    if focal and focal in config.prices:
        price = config.prices[focal]
        mask = result["strategy"] == focal
        result.loc[mask, "K"] = result.loc[mask, "cost"] - price
    else:
        result["K"] = result["cost"]
    return result


def unit_check(effects_unit: str, lambda_values: Optional[Iterable[float]] = None) -> None:
    if lambda_values is None:
        return
    if not isinstance(lambda_values, Iterable):
        raise TypeError("lambda_values must be iterable")
    # Placeholder: in the future we might assert that willingness-to-pay is in
    # currency per effects_unit. For now we check for emptiness and numeric type.
    for value in lambda_values:
        if value is None:
            raise ValueError("Willingness-to-pay grid contains None values")
        if not np.isfinite(value):
            raise ValueError("Willingness-to-pay grid contains non-finite values")


def assert_strategy_presence(df: pd.DataFrame, perspective: str, strategies: List[str]) -> tuple[List[str], List[str]]:
    """Check which strategies are present in the PSA data for a given perspective.
    
    Returns (present, missing) lists. Logs warnings for missing strategies but does not raise.
    """
    available = set(df[(df["perspective"] == perspective)]["strategy"].unique())
    present = [s for s in strategies if s in available]
    missing = [s for s in strategies if s not in available]
    
    if missing:
        print(f"WARNING: Strategies missing in {perspective} perspective: {', '.join(missing)}")
        print(f"Available strategies: {', '.join(sorted(available))}")
    
    return present, missing


def load_analysis_inputs(psa_path: Path, config_path: Path, perspective: str, focal: Optional[str] = None, lambda_grid: Optional[Iterable[float]] = None) -> PSAData:
    config = StrategyConfig.from_yaml(config_path)
    resolved_perspective = normalise_perspective(perspective, config.perspectives)

    psa = load_psa(psa_path)
    psa = filter_perspective(psa, resolved_perspective)
    psa = ensure_strategy_overlap(psa, config.strategies)
    psa = align_draws(psa)

    psa = compute_price_adjusted_costs(psa, config, focal=focal)
    unit_check(config.effects_unit, lambda_grid)

    return PSAData(table=psa, config=config, perspective=resolved_perspective)