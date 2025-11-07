#!/usr/bin/env python3
"""
Compute a probabilistic "tornado" using Partial Rank Correlation Coefficients (PRCC).

CLI:
  --psa <csv>                       PSA with parameter columns (param_*)
  --strategy "Oral ketamine"        Focal therapy
  --base "Usual care"               Base comparator
  --perspective {health_system,societal}
  --lambda 50000                    Willingness-to-pay per effect unit
  --top 12                          Number of top |PRCC| parameters to plot
  --outdir <dir>                    Output directory for CSV and figure

If no param_* columns exist in the PSA, exits 0 and writes a TODO message suggesting
using OWSA in a follow-up step.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis_core.io import load_psa, filter_perspective, align_draws, assert_strategy_presence  # noqa: E402
from analysis_core.plotting import figure_context, save_multiformat  # noqa: E402
from utils import set_seed


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Make probabilistic tornado via PRCC on INB vs params")
    p.add_argument("--psa", type=Path, required=True, help="PSA CSV with parameter columns (param_*)")
    p.add_argument("--strategy", type=str, required=True, help="Focal strategy name")
    p.add_argument("--base", type=str, required=True, help="Base comparator name")
    p.add_argument("--perspective", choices=["health_system", "societal"], required=True)
    p.add_argument("--lambda", dest="lam", type=float, required=True, help="Willingness-to-pay")
    p.add_argument("--top", type=int, default=12, help="Top |PRCC| parameters to plot (default: 12)")
    p.add_argument("--outdir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=12345, help="Random seed for reproducibility")
    return p.parse_args(argv)


def _collect_param_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if c.startswith("param_")]


def compute_inb_per_draw(df: pd.DataFrame, strategy: str, base: str, lam: float) -> pd.DataFrame:
    # Expect df filtered to one perspective and aligned draws across strategies
    df_s = df[df["strategy"] == strategy].set_index("draw")[["cost", "effect"]].rename(
        columns={"cost": "C_i", "effect": "E_i"}
    )
    df_b = df[df["strategy"] == base].set_index("draw")[["cost", "effect"]].rename(
        columns={"cost": "C_base", "effect": "E_base"}
    )
    merged = df_s.join(df_b, how="inner").reset_index()
    merged["dE"] = merged["E_i"] - merged["E_base"]
    merged["dC"] = merged["C_i"] - merged["C_base"]
    merged["INB"] = lam * merged["dE"] - merged["dC"]
    return merged[["draw", "dE", "dC", "INB"]]


def rank_transform(df: pd.DataFrame) -> pd.DataFrame:
    # Average ranks, normalized to [1, n]
    return df.rank(method="average")


def prcc(inb_r: np.ndarray, Xr: np.ndarray, names: List[str]) -> pd.DataFrame:
    # Compute PRCC via residual correlation method after rank-transform
    n, p = Xr.shape
    results = []
    # Precompute once the intercept-augmented matrices for each leave-one-out
    for j in range(p):
        mask = np.ones(p, dtype=bool)
        mask[j] = False
        X_except = Xr[:, mask]
        # Add intercept
        X_e = np.column_stack([np.ones(n), X_except])
        # Residuals of INB on others
        beta_y, *_ = np.linalg.lstsq(X_e, inb_r, rcond=None)
        rY = inb_r - X_e @ beta_y
        # Residuals of X_j on others
        xj = Xr[:, j]
        beta_xj, *_ = np.linalg.lstsq(X_e, xj, rcond=None)
        rXj = xj - X_e @ beta_xj
        # Correlation of residuals
        denom = np.std(rY, ddof=1) * np.std(rXj, ddof=1)
        if denom == 0 or not np.isfinite(denom):
            r = 0.0
        else:
            r = float(np.corrcoef(rY, rXj)[0, 1])
            if not np.isfinite(r):
                r = 0.0
        results.append((names[j], r, abs(r), "positive" if r >= 0 else "negative"))
    out = pd.DataFrame(results, columns=["parameter", "prcc", "abs_prcc", "sign"]).sort_values(
        "abs_prcc", ascending=False
    ).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1)
    return out


def run(psa_path: Path, strategy: str, base: str, perspective: str, lam: float, top: int, outdir: Path, seed: int = 12345) -> int:
    set_seed(seed)
    outdir.mkdir(parents=True, exist_ok=True)
    df = load_psa(psa_path)
    
    # Check for strategy presence
    present_strategies, missing_strategies = assert_strategy_presence(
        df, perspective, [strategy, base]
    )
    if base not in present_strategies:
        skip_note = f"PRCC tornado analysis skipped: base strategy '{base}' not found in PSA data for {perspective} perspective."
        (outdir / "SKIP").write_text(skip_note)
        print(skip_note)
        return 0
    if strategy not in present_strategies:
        skip_note = f"PRCC tornado analysis skipped: focal strategy '{strategy}' not found in PSA data for {perspective} perspective."
        (outdir / "SKIP").write_text(skip_note)
        print(skip_note)
        return 0
    
    df = filter_perspective(df, perspective)
    df = df[df["strategy"].isin([strategy, base])].copy()
    if df.empty:
        print(f"No rows for strategy='{strategy}' and base='{base}' in perspective='{perspective}'.")
        return 0
    df = align_draws(df)

    param_cols = _collect_param_cols(df)
    if not param_cols:
        # Write a TODO note and exit 0 per spec
        todo = outdir / "TODO_NO_PARAM_COLUMNS.txt"
        todo.write_text(
            "No param_* columns found in PSA. Skipping PRCC tornado.\n"
            "Consider running one-way sensitivity analysis (OWSA) in the next step.\n",
            encoding="utf-8",
        )
        print(todo.read_text())
        return 0

    # Parameters should be per-draw; take them from base rows to avoid duplicates
    params_by_draw = (
        df[df["strategy"] == base][["draw"] + param_cols]
        .drop_duplicates("draw")
        .set_index("draw")
        .sort_index()
    )

    inb = compute_inb_per_draw(df, strategy=strategy, base=base, lam=lam).set_index("draw").sort_index()

    merged = params_by_draw.join(inb[["INB"]], how="inner").dropna(axis=0, how="any")
    if merged.empty:
        print("No complete cases after merging parameters with INB.")
        return 0

    # Rank-transform
    Xr = rank_transform(merged[param_cols]).to_numpy(dtype=float)
    Yr = rank_transform(merged[["INB"]]).to_numpy(dtype=float).ravel()

    coeffs = prcc(Yr, Xr, names=param_cols)

    # Save full coefficients CSV and top-N
    coeffs_path = outdir / "tornado_prcc_coefficients.csv"
    coeffs.to_csv(coeffs_path, index=False)

    top_n = coeffs.head(min(top, len(coeffs))).copy()

    # Plot
    title = f"PRCC Tornado — {strategy} vs {base} ({perspective.replace('_',' ').title()})"
    with figure_context(title, xlabel="PRCC (partial rank correlation)", ylabel="Parameter") as (fig, ax):
        y = np.arange(len(top_n))[::-1]
        colors = np.where(top_n["prcc"] >= 0, "#1f77b4", "#ff7f0e")
        ax.barh(y, top_n["prcc"].to_numpy(float)[::-1], color=colors[::-1])
        ax.set_yticks(y, labels=top_n["parameter"][::-1])
        ax.set_xlim(-1, 1)
        ax.axvline(0, color="#999999", linestyle=":", linewidth=1)
        save_multiformat(fig, outdir, "tornado_prcc")
        plt.close(fig)

    return 0


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    return run(args.psa, args.strategy, args.base, args.perspective, args.lam, args.top, args.outdir, args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
