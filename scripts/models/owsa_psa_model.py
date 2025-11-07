#!/usr/bin/env python3
"""
Deterministic stub model for OWSA.

Contract:
  python scripts/owsa_psa_model.py --params inputs/base_params.yaml \
    --strategy "Oral ketamine" --base "Usual care" \
    --perspective societal --lambda 50000

Prints JSON to stdout with keys {"dE": float, "dC": float} representing
incremental effectiveness (QALYs) and cost (currency units) for the given
strategy versus base, for the parameters provided.

This is a toy model to enable end-to-end OWSA runs. Replace with your actual
model logic when ready.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import yaml


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deterministic stub model for OWSA")
    p.add_argument("--params", type=Path, required=True)
    p.add_argument("--strategy", type=str, required=True)
    p.add_argument("--base", type=str, required=True)
    p.add_argument("--perspective", choices=["health_system", "societal"], required=True)
    p.add_argument("--lambda", dest="lam", type=float, required=True)
    return p.parse_args()


def _get(d: Dict[str, Any], path: str, default: Any) -> Any:
    cur = d
    for k in path.split('.'):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def main() -> int:
    args = parse_args()
    with args.params.open("r", encoding="utf-8") as f:
        params = yaml.safe_load(f) or {}

    # Read parameters with defaults
    consult = float(_get(params, "costs.consultation_fee", 120.0))
    session_cost = float(_get(params, "costs.session_cost", 300.0))
    monitoring = float(_get(params, "costs.monitoring_per_session", 45.0))
    n_sessions = float(_get(params, "costs.n_sessions", 6))

    resp = float(_get(params, "effectiveness.response_rate", 0.40))
    rem = float(_get(params, "effectiveness.remission_rate", 0.25))

    qaly_gain = float(_get(params, "utilities.qaly_gain", 0.08))

    # Simple toy relationships for illustration only
    # Incremental cost: consultation + per-session costs vs base (assume base cost 0)
    dC = consult + n_sessions * (session_cost + monitoring)

    # Societal perspective could include a nominal 5% uplift (e.g., productivity); illustrative only
    if args.perspective == "societal":
        dC *= 1.05

    # Incremental QALYs: base on qaly_gain scaled by response/remission influence
    # Ensure reasonable bounds
    eff_scale = max(0.0, min(1.5, 0.5 + 0.25 * resp + 0.25 * rem))
    dE = qaly_gain * eff_scale

    # Output JSON
    print(json.dumps({"dE": float(dE), "dC": float(dC)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
