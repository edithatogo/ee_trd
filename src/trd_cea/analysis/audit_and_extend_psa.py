#!/usr/bin/env python3
"""Audit and optionally extend PSA datasets with additional therapy draws.

This CLI tool validates a PSA dataset, checks whether a focal therapy already
exists, and if not, attempts to source draws from existing CSVs, an explicit
input file, or by simulating from parameter distributions. As a last resort it
can trigger an evidence fetch workflow.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Setup logging infrastructure
script_dir = Path(__file__).resolve().parent
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

import argparse
import csv
import datetime as dt
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd
import yaml

try:
    from utils import set_seed
except ImportError:  # pragma: no cover - fallback for standalone usage
    def set_seed(seed: Optional[int] = None) -> int:
        np.random.seed(12345 if seed is None else seed)
        return 12345 if seed is None else seed


REQUIRED_COLUMNS = {"strategy", "draw", "cost", "effect", "perspective"}
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUTS_DIR = PROJECT_ROOT / "inputs"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
FETCH_SCRIPT = SCRIPT_DIR / "fetch_new_evidence.py"
DEFAULT_SEED = 12345


class AuditError(Exception):
    """Raised when validation fails."""


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and extend PSA draws")
    parser.add_argument("--psa", type=Path, default=DATA_DIR / "psa.csv")
    parser.add_argument("--strategies-yaml", type=Path, default=PROJECT_ROOT / "config" / "strategies.yml")
    parser.add_argument("--perspective", choices=["health_system", "societal"], required=True)
    parser.add_argument("--add-therapy", default="Oral ketamine", help="Therapy name to ensure is present")
    parser.add_argument("--price-current-override", type=float, default=None)
    parser.add_argument("--from-csv", dest="from_csv", type=Path, default=None)
    parser.add_argument("--from-params", dest="from_params", type=Path, default=None)
    parser.add_argument("--auto-search", action="store_true")
    parser.add_argument("--out", type=Path, default=DATA_DIR / "psa_extended.csv")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args(argv)


def load_strategy_config(path: Path) -> dict:
    if not path.exists():
        raise AuditError(f"Strategy config not found at '{path}'")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    required = {"base", "perspectives", "strategies", "prices"}
    missing = required - set(data)
    if missing:
        raise AuditError(
            "Strategy config missing required keys: " + ", ".join(sorted(missing))
        )
    data["perspectives"] = list(data.get("perspectives", []))
    data["strategies"] = list(data.get("strategies", []))
    return data


def normalise_perspective(requested: str, available: List[str]) -> str:
    if requested in available:
        return requested
    lookup = {p.lower().replace("_", ""): p for p in available}
    key = requested.lower().replace("_", "")
    if key in lookup:
        return lookup[key]
    raise AuditError(
        f"Perspective '{requested}' not present in config. Available: {available}"
    )


def load_psa(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise AuditError(f"PSA file not found at '{path}'")
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise AuditError(
            "PSA file missing required columns: " + ", ".join(sorted(missing))
        )
    return df


def validate_psa(df: pd.DataFrame, perspective: str) -> pd.DataFrame:
    subset = df[df["perspective"] == perspective].copy()
    if subset.empty:
        raise AuditError(
            f"No PSA rows found for perspective '{perspective}'"
        )
    if subset[list(REQUIRED_COLUMNS)].isna().any().any():
        raise AuditError("PSA subset contains NaN values in required columns")

    draw_groups = subset.groupby("strategy")["draw"]
    reference_draws = None
    for strategy, draws in draw_groups:
        draws_sorted = np.sort(draws.unique())
        if reference_draws is None:
            reference_draws = draws_sorted
        elif not np.array_equal(reference_draws, draws_sorted):
            raise AuditError(
                f"Draw IDs misaligned for strategy '{strategy}' (expected identical sets)"
            )
    return subset


def find_existing_strategy(psa_subset: pd.DataFrame, therapy: str) -> bool:
    return therapy in psa_subset["strategy"].unique()


def scan_repo_for_strategy(therapy: str, perspective: str) -> List[pd.DataFrame]:
    matches: List[pd.DataFrame] = []
    for base_dir in (DATA_DIR, INPUTS_DIR):
        if not base_dir.exists():
            continue
        for path in base_dir.rglob("*.csv"):
            try:
                df = pd.read_csv(path)
            except Exception:
                continue
            if set(REQUIRED_COLUMNS).issubset(df.columns):
                subset = df[
                    (df["strategy"] == therapy) & (df["perspective"] == perspective)
                ].copy()
                if not subset.empty:
                    subset["__source_path"] = str(path)
                    matches.append(subset)
    return matches


def align_draws(new_df: pd.DataFrame, base_draws: np.ndarray, report: List[str]) -> pd.DataFrame:
    draws = np.sort(new_df["draw"].unique())
    if np.array_equal(draws, base_draws):
        return new_df
    if len(draws) != len(base_draws):
        raise AuditError(
            "New data draw count mismatch; expected "
            f"{len(base_draws)}, got {len(draws)}"
        )
    report.append(
        "Reindexing new therapy draws to align with existing PSA draw IDs"
    )
    order = new_df.sort_values("draw").index
    reindexed = new_df.loc[order].copy()
    reindexed["draw"] = base_draws
    return reindexed


def load_extension_from_csv(path: Path, therapy: str, perspective: str, base_draws: np.ndarray, report: List[str]) -> pd.DataFrame:
    if not path.exists():
        raise AuditError(f"Extension CSV not found at '{path}'")
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise AuditError(
            "Extension CSV missing required columns: " + ", ".join(sorted(missing))
        )
    subset = df[
        (df["strategy"] == therapy) & (df["perspective"] == perspective)
    ].copy()
    if subset.empty:
        raise AuditError(
            f"Extension CSV contains no rows for therapy='{therapy}', perspective='{perspective}'"
        )
    subset = align_draws(subset, base_draws, report)
    subset["__source_path"] = str(path)
    return subset


# ---------------------------------------------------------------------------
# Simulation utilities
# ---------------------------------------------------------------------------


def sample_distribution(spec: dict, size: int) -> np.ndarray:
    # Accept both 'distribution' and 'dist' keys
    dist = (spec.get("distribution") or spec.get("dist") or "normal").lower()
    if dist == "normal":
        mean = spec.get("mean")
        sd = spec.get("sd")
        if mean is None or sd is None:
            raise AuditError("Normal distribution requires 'mean' and 'sd'")
        return np.random.normal(mean, sd, size)
    if dist == "lognormal":
        mean = spec.get("mean")
        sigma = spec.get("sigma")
        if mean is None or sigma is None:
            raise AuditError("Lognormal distribution requires 'mean' and 'sigma'")
        return np.random.lognormal(mean, sigma, size)
    if dist == "gamma":
        shape = spec.get("shape")
        scale = spec.get("scale", 1.0)
        if shape is None:
            raise AuditError("Gamma distribution requires 'shape'")
        return np.random.gamma(shape, scale, size)
    if dist == "uniform":
        low = spec.get("low")
        high = spec.get("high")
        if low is None or high is None:
            raise AuditError("Uniform distribution requires 'low' and 'high'")
        return np.random.uniform(low, high, size)
    if dist in {"fixed", "constant"}:
        value = spec.get("value")
        if value is None:
            raise AuditError("Fixed distribution requires 'value'")
        return np.full(size, value)
    raise AuditError(f"Unsupported distribution '{dist}' in parameter YAML")


def simulate_from_params(params_path: Path, therapy: str, perspective: str, base_data: pd.DataFrame, price_override: Optional[float], report: List[str]) -> pd.DataFrame:
    if not params_path.exists():
        raise AuditError(f"Parameter YAML not found at '{params_path}'")
    with params_path.open("r", encoding="utf-8") as handle:
        params = yaml.safe_load(handle) or {}

    delta_effect_spec = params.get("delta_effect")
    # Accept multiple aliases; this represents ΔK_fixed (excludes price)
    delta_cost_spec = (
        params.get("delta_cost_fixed_K")
        or params.get("delta_fixed_cost")
        or params.get("delta_cost")
    )
    price_current = price_override if price_override is not None else (
        params.get("price_current") if params.get("price_current") is not None else params.get("price")
    )
    if price_current is None:
        raise AuditError("Price must be provided via --price-current-override or parameter YAML 'price_current'/'price'")
    if delta_effect_spec is None:
        raise AuditError("Parameter YAML missing 'delta_effect' section")
    if delta_cost_spec is None:
        raise AuditError("Parameter YAML missing 'delta_cost_fixed_K' (or 'delta_fixed_cost'/'delta_cost') section")

    draws = np.sort(base_data["draw"].unique())
    n = len(draws)
    delta_e = sample_distribution(delta_effect_spec, n)
    delta_k = sample_distribution(delta_cost_spec, n)

    base_sorted = base_data.sort_values("draw")
    base_effect = base_sorted["effect"].to_numpy()
    base_cost = base_sorted["cost"].to_numpy()

    # Compose per spec: E_i = E_base + ΔE; K_i = C_base + ΔK_fixed; cost_i = K_i + price_current
    effect = base_effect + delta_e
    K_i = base_cost + delta_k
    cost = K_i + float(price_current)

    simulated = pd.DataFrame(
        {
            "strategy": therapy,
            "draw": draws,
            "cost": cost,
            "effect": effect,
            "perspective": perspective,
        }
    )
    simulated["__source_path"] = str(params_path)
    report.append(
        "Simulated new therapy draws from parameter YAML"
    )
    return simulated


# ---------------------------------------------------------------------------
# Evidence fetch workflow
# ---------------------------------------------------------------------------


def sanitise_name(name: str) -> str:
    return name.lower().replace(" ", "_")


def run_auto_search(therapy: str, dry_run: bool, report: List[str]) -> None:
    stamp = dt.datetime.now().strftime("%Y%m%d")
    folder = EVIDENCE_DIR / f"feat_{sanitise_name(therapy)}_{stamp}"
    candidates = folder / "candidates.csv"

    if dry_run:
        report.append(
            f"[dry-run] Would create {candidates} after calling fetch_new_evidence.py"
        )
        return

    folder.mkdir(parents=True, exist_ok=True)
    fetch_cmd = [sys.executable, str(FETCH_SCRIPT), "--therapy", therapy, "--out", str(candidates)]
    if FETCH_SCRIPT.exists():
        subprocess.run(fetch_cmd, check=False)
    else:
        with candidates.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["source", "note"])
            writer.writerow(["N/A", "fetch_new_evidence.py missing; placeholder only"])
    report.append(
        "Auto-search triggered. Review evidence folder and integrate candidates manually."
    )
    print("TODO: Review fetched evidence, assess quality, and rerun audit once data available.")


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    report: List[str] = []

    set_seed(args.seed)

    config = load_strategy_config(args.strategies_yaml)
    perspective_config = normalise_perspective(args.perspective, config["perspectives"])
    therapy = args.add_therapy

    if therapy not in config["strategies"]:
        report.append(
            f"Therapy '{therapy}' not listed in config strategies; proceeding regardless"
        )

    psa = load_psa(args.psa)
    psa_subset = validate_psa(psa, perspective_config)
    base_draws = np.sort(psa_subset["draw"].unique())

    if find_existing_strategy(psa_subset, therapy):
        report.append("Therapy already present in PSA; no extension required")
        extended = psa
    else:
        report.append("Therapy absent from PSA; attempting to source new draws")
        matches = scan_repo_for_strategy(therapy, perspective_config)
        new_rows: Optional[pd.DataFrame] = None
        if matches:
            match = matches[0]
            report.append(
                f"Found existing draws in {match['__source_path'].iat[0]}"
            )
            new_rows = align_draws(match.drop(columns=["__source_path"]), base_draws, report)
        elif args.from_csv is not None:
            report.append(f"Reading extension data from {args.from_csv}")
            new_rows = load_extension_from_csv(args.from_csv, therapy, perspective_config, base_draws, report)
        elif args.from_params is not None:
            # Load params to determine reference strategy for draws if specified
            with args.from_params.open("r", encoding="utf-8") as handle:
                params_preview = yaml.safe_load(handle) or {}
            base_strategy = params_preview.get("draws_like") or config.get("base")
            if base_strategy not in psa_subset["strategy"].unique():
                raise AuditError(
                    f"Reference strategy for draws ('{base_strategy}') not present in PSA"
                )
            base_data = psa_subset[psa_subset["strategy"] == base_strategy]
            report.append(
                f"Simulating draws using parameters from {args.from_params} (draws_like='{base_strategy}')"
            )
            new_rows = simulate_from_params(
                args.from_params,
                therapy,
                perspective_config,
                base_data,
                args.price_current_override if args.price_current_override is not None else config.get("prices", {}).get(therapy),
                report,
            )
        elif args.auto_search:
            report.append("No data found; triggering auto-search workflow")
            run_auto_search(therapy, args.dry_run, report)
            print("Audit complete (auto-search triggered).")
            return 0
        else:
            raise AuditError(
                "Therapy not found and no data source provided (--from-csv, --from-params, or --auto-search)."
            )

        if new_rows is None:
            raise AuditError("Internal error: failed to obtain new therapy rows")

        if "__source_path" in new_rows.columns:
            new_rows = new_rows.drop(columns=["__source_path"])

        extended = pd.concat([psa, new_rows], ignore_index=True)
        report.append(
            f"Extended PSA with {len(new_rows)} draws for '{therapy}'"
        )

    if args.dry_run:
        report.append(f"[dry-run] Would write extended PSA to {args.out}")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        extended.to_csv(args.out, index=False)
        report.append(f"Wrote extended PSA to {args.out}")

    print("Audit report:")
    for item in report:
        print(f" - {item}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AuditError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
