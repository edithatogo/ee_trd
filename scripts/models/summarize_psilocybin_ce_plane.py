#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import pandas as pd


def summarize(deltas_csv: Path) -> dict:
    df = pd.read_csv(deltas_csv)
    dE = df["dE"].to_numpy()
    dC = df["dC"].to_numpy()
    n = max(1, dE.size)
    ne = int(((dE > 0) & (dC > 0)).sum())
    nw = int(((dE < 0) & (dC > 0)).sum())
    se = int(((dE > 0) & (dC < 0)).sum())
    sw = int(((dE < 0) & (dC < 0)).sum())
    dominant = int(((dE > 0) & (dC < 0)).sum())
    dominated = int(((dE < 0) & (dC > 0)).sum())
    return {
        "n": n,
        "NE": ne / n,
        "NW": nw / n,
        "SE": se / n,
        "SW": sw / n,
        "dominant": dominant,
        "dominated": dominated,
    }


def write_summary(root: Path, perspective: str, stats: dict) -> None:
    md = [f"### Psilocybin-assisted therapy vs base — {perspective.replace('_',' ').title()}\n"]
    md.append(f"n draws: {stats['n']}")
    md.append(
        f"Quadrants: NE {stats['NE']*100:0.1f}%, NW {stats['NW']*100:0.1f}%, SE {stats['SE']*100:0.1f}%, SW {stats['SW']*100:0.1f}%"
    )
    md.append(f"Dominant (ΔE>0, ΔC<0): {stats['dominant']}")
    md.append(f"Dominated (ΔE<0, ΔC>0): {stats['dominated']}")
    out = root / "psilocybin_inclusion_summary.md"
    with out.open("a", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--perspective", choices=["health_system", "societal"], required=True)
    args = p.parse_args()

    if args.perspective == "societal":
        deltas = args.root / "ce_plane" / "therapy_c" / "deltas.csv"
    else:
        deltas = args.root / "ce_plane_hs" / "therapy_c" / "deltas.csv"
    stats = summarize(deltas)
    write_summary(args.root, args.perspective, stats)


if __name__ == "__main__":
    main()
