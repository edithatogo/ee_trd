#!/usr/bin/env python3
"""
One-way sensitivity analysis (OWSA) tornado wrapper.

CLI:
  --base-params inputs/base_params.yaml
  --range inputs/owsa_ranges.yaml
  --model scripts/owsa_psa_model.py
  --strategy "Oral ketamine"
  --base "Usual care"
  --perspective {health_system,societal}
  --lambda 50000
  --top 12
  --outdir results/feat_oral_ketamine_YYYYMMDD/tornado_owsa

Expected model contract:
  python scripts/owsa_psa_model.py --params <params.yaml> --strategy <name> --base <name> --perspective <p> --lambda <lam>
  ...prints JSON with keys {"dE": <float>, "dC": <float>} representing incremental values at the given params.

Behavior:
  - If model script does not exist, exit 0 and write a TODO message suggesting filling in the model.
  - Otherwise, for each parameter in range YAML, evaluate at low/high, record ΔINB between high and low, and plot a classic tornado.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
import copy
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from utils import set_seed

try:  # Prefer project plotting utils; otherwise fall back to a local minimal version
    from analysis_core.plotting import figure_context, save_multiformat, write_caption  # type: ignore  # noqa: E402
except Exception:  # pragma: no cover
    from contextlib import contextmanager

    @contextmanager
    def figure_context(title: str | None = None, xlabel: str | None = None, ylabel: str | None = None):
        fig, ax = plt.subplots(figsize=(8, 5))
        if title:
            ax.set_title(title)
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        try:
            yield fig, ax
        finally:
            pass

    def save_multiformat(fig, outdir: Path, basename: str, formats: list[str] | None = None, dpi: int = 300):
        outdir.mkdir(parents=True, exist_ok=True)
        fmts = formats or ["png", "pdf"]
        for ext in fmts:
            fig.savefig(outdir / f"{basename}.{ext}", dpi=dpi, bbox_inches="tight")

    def write_caption(outdir: Path, filename: str, text: str) -> Path:
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / filename
        path.write_text(text.strip() + "\n", encoding="utf-8")
        return path


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run OWSA tornado by calling an external model")
    p.add_argument("--base-params", type=Path, required=True)
    p.add_argument("--range", dest="range_yaml", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--strategy", type=str, required=True)
    p.add_argument("--base", type=str, required=True)
    p.add_argument("--perspective", choices=["health_system", "societal"], required=True)
    p.add_argument("--lambda", dest="lam", type=float, required=True)
    p.add_argument("--top", type=int, default=12)
    p.add_argument("--outdir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=12345, help="Random seed for reproducibility")
    return p.parse_args(argv)


def _load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _set_deep(d: Dict, dotted_key: str, value):
    """Set a nested key in a possibly nested dict using dot-path notation."""
    keys = dotted_key.split(".")
    cur = d
    for k in keys[:-1]:
        nxt = cur.get(k)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[k] = nxt
        cur = nxt
    cur[keys[-1]] = value


def _call_model(model: Path, params_path: Path, strategy: str, base: str, perspective: str, lam: float) -> Tuple[float, float]:
    cmd = [
        sys.executable,
        str(model),
        "--params",
        str(params_path),
        "--strategy",
        strategy,
        "--base",
        base,
        "--perspective",
        perspective,
        "--lambda",
        str(lam),
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
    stdout = proc.stdout.strip()
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Model did not return valid JSON. stdout=\n{stdout}\n\nstderr=\n{proc.stderr}") from exc
    return float(data["dE"]), float(data["dC"])


def run(base_params: Path, range_yaml: Path, model: Path, strategy: str, base: str, perspective: str, lam: float, top: int, outdir: Path, seed: int = 12345) -> int:
    set_seed(seed)
    outdir.mkdir(parents=True, exist_ok=True)
    if not model.exists():
        todo = outdir / "TODO_NO_MODEL_SCRIPT.txt"
        todo.write_text(
            "OWSA model script not found. Provide a callable model at the --model path with CLI contract described in make_tornado_owsa.py.\n",
            encoding="utf-8",
        )
        print(todo.read_text())
        return 0

    base_cfg = _load_yaml(base_params)
    ranges = _load_yaml(range_yaml)

    results = []
    for name, bounds in (ranges or {}).items():
        if not isinstance(bounds, dict) or "low" not in bounds or "high" not in bounds:
            continue
        low_cfg = copy.deepcopy(base_cfg)
        high_cfg = copy.deepcopy(base_cfg)
        _set_deep(low_cfg, name, bounds["low"])
        _set_deep(high_cfg, name, bounds["high"])

        # Write temp parameter files
        low_path = outdir / f"tmp_{name}_low.yaml"
        high_path = outdir / f"tmp_{name}_high.yaml"
        with low_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(low_cfg, f)
        with high_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(high_cfg, f)

        dE_low, dC_low = _call_model(model, low_path, strategy, base, perspective, lam)
        dE_high, dC_high = _call_model(model, high_path, strategy, base, perspective, lam)

        inb_low = lam * dE_low - dC_low
        inb_high = lam * dE_high - dC_high
        delta_inb = inb_high - inb_low
        results.append((name, inb_low, inb_high, delta_inb))

    if not results:
        print("No valid ranges found or model produced no outputs.")
        return 0

    df = pd.DataFrame(results, columns=["parameter", "inb_low", "inb_high", "delta_inb"]).sort_values(
        "delta_inb", key=lambda s: s.abs(), ascending=False
    )

    csv_path = outdir / "tornado_owsa.csv"
    df.to_csv(csv_path, index=False)

    # Plot classic tornado: bars from min(INB_low, INB_high) to max(...)
    top_n = df.head(min(top, len(df))).copy()
    y = np.arange(len(top_n))[::-1]

    with figure_context(
        title=f"OWSA Tornado — {strategy} vs {base} ({perspective.replace('_',' ').title()})",
        xlabel="Incremental net benefit (INB)",
        ylabel="Parameter",
    ) as (fig, ax):
        lows = np.minimum(top_n["inb_low"], top_n["inb_high"]).to_numpy(float)[::-1]
        highs = np.maximum(top_n["inb_low"], top_n["inb_high"]).to_numpy(float)[::-1]
        widths = highs - lows
        bars = ax.barh(y, widths, left=lows, color="#1f77b4")
        ax.set_yticks(y, labels=top_n["parameter"][::-1])
        ax.axvline(0, color="#999999", linestyle=":", linewidth=1)
        # Add value labels showing signed ΔINB (high − low) from original ordering
        deltas = top_n["delta_inb"].to_numpy(float)[::-1]
        for i, (bar, delta, hi) in enumerate(zip(bars, deltas, highs)):
            x = bar.get_x() + bar.get_width()
            # Place label near the right edge with a small offset; fallback to hi if bar width is tiny
            xpos = x if bar.get_width() > 1e-9 else hi
            ax.text(
                xpos + 0.01 * (ax.get_xlim()[1] - ax.get_xlim()[0]),
                bar.get_y() + bar.get_height() / 2,
                f"{delta:+,.0f}",
                va="center",
                ha="left",
                fontsize=9,
                color="#333333",
            )
        save_multiformat(fig, outdir, "tornado_owsa")
        plt.close(fig)

    # Write a simple publication-style caption
    top_list = ", ".join(top_n["parameter"]) if not top_n.empty else "(none)"
    cap = (
        f"Tornado diagram of one-way sensitivity analysis for {strategy} vs {base} under the {perspective.replace('_',' ')} perspective. "
        f"Bars show the range of incremental net benefit (INB = λ×ΔE − ΔC) when varying each parameter between its specified low and high bounds. "
        f"Willingness-to-pay λ = {lam:,.0f}. Top {len(top_n)} parameters shown: {top_list}."
    )
    write_caption(outdir, "tornado_owsa_caption.md", cap)

    return 0


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    return run(args.base_params, args.range_yaml, args.model, args.strategy, args.base, args.perspective, args.lam, args.top, args.outdir, args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
