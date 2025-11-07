#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

# Ensure project root is importable (match pattern used in other CLIs)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis_core.io import load_analysis_inputs, assert_strategy_presence
from analysis_core.deltas import compute_deltas
from analysis_core.plotting import (
    figure_context,
    save_multiformat,
    ensure_legend,
    add_vertical_reference,
    add_horizontal_reference,
    write_caption,
)
from analysis_v2.publication import display_name
from utils import set_seed

# ---------------------------------------------------------------------------
# CE plane helpers
# ---------------------------------------------------------------------------


def mean_cov(points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    mu = np.mean(points, axis=0)
    cov = np.cov(points.T)
    return mu, cov


def confidence_ellipse(
    ax: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    *,
    n_std: float = 1.96,
    facecolor: str = "#1f77b4",
    alpha: float = 0.12,
    edgecolor: str = "#1f77b4",
) -> Ellipse | None:
    # Robust 95% confidence ellipse; safe for singular/near-singular covariance
    if x.size < 2:
        return None
    cov = np.cov(x, y)
    try:
        vals, vecs = np.linalg.eigh(cov)
    except Exception:
        return None
    vals = np.atleast_1d(vals)
    if vals.size < 2:
        return None
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]
    vals = np.clip(vals, a_min=0.0, a_max=None)
    if not np.isfinite(vals).all() or vals.max() == 0:
        return None
    theta = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
    width_height = 2 * n_std * np.sqrt(vals[:2])
    if not np.isfinite(width_height).all():
        return None
    ell = Ellipse(
        (np.mean(x), np.mean(y)),
        float(width_height[0]),
        float(width_height[1]),
        angle=float(theta),
        facecolor=facecolor,
        edgecolor=edgecolor,
        lw=1.0,
        alpha=alpha,
    )
    ax.add_patch(ell)
    return ell


def quadrant_proportions(dE: np.ndarray, dC: np.ndarray) -> dict:
    # NE (+,+), NW (-,+), SE (+,-), SW (-,-)
    ne = np.sum((dE > 0) & (dC > 0))
    nw = np.sum((dE < 0) & (dC > 0))
    se = np.sum((dE > 0) & (dC < 0))
    sw = np.sum((dE < 0) & (dC < 0))
    n = max(1, dE.size)
    return {"NE": ne / n, "NW": nw / n, "SE": se / n, "SW": sw / n, "n": int(n)}


def dominance_counts(dE: np.ndarray, dC: np.ndarray) -> Tuple[int, int]:
    # dominant: dE>0 & dC<0; dominated: dE<0 & dC>0
    dominant = int(np.sum((dE > 0) & (dC < 0)))
    dominated = int(np.sum((dE < 0) & (dC > 0)))
    return dominant, dominated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _slugify(name: str) -> str:
    return (
        name.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )


def run(
    psa_path: Path,
    strategies_yaml: Path,
    perspective: str,
    lam: float,
    outdir: Path,
    seed: int | None = None,
) -> None:
    if seed is not None:
        set_seed(seed)
    data = load_analysis_inputs(psa_path, strategies_yaml, perspective)
    base = data.config.base

    available = sorted(set(data.table["strategy"].unique()))
    therapies = [s for s in available if s != base]

    # Check for base strategy presence
    present_strategies, missing_strategies = assert_strategy_presence(
        data.table, perspective, [base] + therapies
    )
    if base not in present_strategies:
        outdir.mkdir(parents=True, exist_ok=True)
        skip_note = f"CE plane analysis skipped: base strategy '{base}' not found in PSA data for {perspective} perspective."
        (outdir / "SKIP").write_text(skip_note)
        print(skip_note)
        return
    if not therapies or all(t not in present_strategies for t in therapies):
        outdir.mkdir(parents=True, exist_ok=True)
        skip_note = f"CE plane analysis skipped: no therapy strategies found in PSA data for {perspective} perspective. Missing: {', '.join(missing_strategies)}"
        (outdir / "SKIP").write_text(skip_note)
        print(skip_note)
        return

    # Filter therapies to only present ones
    therapies = [t for t in therapies if t in present_strategies]
    for therapy in therapies:
        deltas = compute_deltas(data, therapy)
        # Save CSV
        therapy_dir = outdir / _slugify(therapy)
        therapy_dir.mkdir(parents=True, exist_ok=True)
        csv_path = therapy_dir / "deltas.csv"
        deltas.df.to_csv(csv_path, index=False)

        dE = deltas.df["dE"].to_numpy()
        dC = deltas.df["dC"].to_numpy()

        # Plot
        disp = display_name(therapy, data.config)
        base_disp = display_name(base, data.config)
        title = f"Cost-Effectiveness Plane: {disp} vs {base_disp} ({perspective.replace('_',' ').title()})"
        with figure_context(title, xlabel=f"ΔE (vs {base_disp})", ylabel=f"ΔC (vs {base_disp})") as (fig, ax):
            ax.scatter(dE, dC, s=12, alpha=0.6, color="#1f77b4", edgecolors="none", label="PSA draws")
            # 95% ellipse
            confidence_ellipse(ax, dE, dC)
            # WTP line: dC = λ * dE
            xspan = np.linspace(np.nanmin(dE), np.nanmax(dE), 100)
            ax.plot(xspan, lam * xspan, color="#d62728", linestyle="--", linewidth=1.2, label=f"WTP line (λ={lam:,.0f})")
            # Axes crosshairs
            add_vertical_reference(ax, 0.0, label="ΔE=0", color="#999999", linestyle=":")
            add_horizontal_reference(ax, 0.0, label="ΔC=0", color="#999999", linestyle=":")
            ensure_legend(ax, frameon=False, location="best")

            # Inset: quadrant proportions and dominance counts
            inset = ax.inset_axes([0.62, 0.05, 0.35, 0.35])
            inset.scatter(dE, dC, s=6, alpha=0.4, color="#1f77b4", edgecolors="none")
            inset.axvline(0, color="#999999", linestyle=":", linewidth=1)
            inset.axhline(0, color="#999999", linestyle=":", linewidth=1)
            inset.set_xticks([])
            inset.set_yticks([])
            props = quadrant_proportions(dE, dC)
            dom, domd = dominance_counts(dE, dC)
            text = (
                f"NE: {props['NE']*100:4.1f}%\nNW: {props['NW']*100:4.1f}%\n"
                f"SE: {props['SE']*100:4.1f}%\nSW: {props['SW']*100:4.1f}%\n"
                f"dominant: {dom}\n dominated: {domd}\n n: {props['n']}"
            )
            inset.text(0.02, 0.98, text, transform=inset.transAxes, va="top", ha="left", fontsize=8)

            _artifacts = save_multiformat(fig, therapy_dir, f"v2_ceplane_individual_{_slugify(therapy)}_{perspective.lower()}")
            plt.close(fig)

        # Caption
        caption = (
            f"Cost-effectiveness plane for {disp} versus {base_disp} in the {perspective.replace('_',' ').title()} perspective. "
            f"Points plot per-draw incremental effects ΔE and incremental costs ΔC relative to {base_disp}. "
            f"The dashed line depicts willingness-to-pay (λ) with slope λ={lam:,.0f} {data.config.currency}/{data.config.effects_unit}. "
            f"Inset shows quadrant proportions (NE, NW, SE, SW), counts of dominant (ΔE>0, ΔC<0) and dominated (ΔE<0, ΔC>0) draws, and total draws."
        )
        write_caption(therapy_dir, f"Figure_ce_plane_{_slugify(therapy)}.caption.md", caption)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Make cost-effectiveness plane plots per therapy vs base")
    p.add_argument("--psa", required=True, help="Path to PSA CSV")
    p.add_argument("--strategies-yaml", required=True, help="Path to strategies YAML")
    p.add_argument("--perspective", required=True, choices=["health_system", "societal"], help="Perspective")
    p.add_argument("--lambda", dest="lam", type=float, required=True, help="Willingness-to-pay per effect unit")
    p.add_argument("--outdir", required=True, help="Output directory for ce plane artifacts")
    p.add_argument("--seed", type=int, default=12345)
    return p.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    run(Path(args.psa), Path(args.strategies_yaml), args.perspective, args.lam, Path(args.outdir), seed=args.seed)


if __name__ == "__main__":
    main()
