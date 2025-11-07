#!/usr/bin/env python3
"""Expected Value of Perfect Information (EVPI) analysis for V2."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis_core.io import load_analysis_inputs
from analysis_core.plotting import figure_context, save_multiformat
from utils import set_seed

def net_monetary_benefit(effects, costs, lambda_val):
    """Calculate net monetary benefit: lambda * effects - costs"""
    return lambda_val * np.array(effects) - np.array(costs)

def calculate_evpi(
    psa_df: pd.DataFrame,
    strategies: list,
    lambda_grid: np.ndarray
) -> pd.DataFrame:
    """Calculate EVPI across WTP thresholds."""
    
    results = []
    
    for lam in lambda_grid:
        # Calculate NMB for each strategy
        strategy_nmbs = {}
        for strategy in strategies:
            strat_data = psa_df[psa_df['strategy'] == strategy]
            if not strat_data.empty:
                nmb = net_monetary_benefit(strat_data['effect'].values, 
                                         strat_data['cost'].values, lam)
                strategy_nmbs[strategy] = nmb
        
        if len(strategy_nmbs) < 2:
            continue
        
        # Expected value with current information (mean NMB)
        mean_nmbs = {k: np.mean(v) for k, v in strategy_nmbs.items()}
        best_strategy = max(mean_nmbs, key=mean_nmbs.get)
        evci = mean_nmbs[best_strategy]
        
        # Expected value with perfect information
        # For each draw, choose the best strategy
        n_draws = len(next(iter(strategy_nmbs.values())))
        evpi_draws = []
        
        for draw_idx in range(n_draws):
            draw_nmbs = {k: v[draw_idx] for k, v in strategy_nmbs.items()}
            best_nmb = max(draw_nmbs.values())
            evpi_draws.append(best_nmb)
        
        evppi = np.mean(evpi_draws)
        evpi = evppi - evci
        
        results.append({
            'lambda': lam,
            'evci': evci,
            'evppi': evppi,
            'evpi': max(0, evpi),  # EVPI cannot be negative
            'evpi_per_person': max(0, evpi)
        })
    
    return pd.DataFrame(results)

def plot_evpi(
    evpi_df: pd.DataFrame,
    perspective: str,
    outdir: Path,
    population_size: int = 1000
) -> None:
    """Plot EVPI curve."""
    
    # Calculate population EVPI
    evpi_df_plot = evpi_df.copy()
    evpi_df_plot['evpi_population'] = evpi_df_plot['evpi'] * population_size
    
    with figure_context(
        title=f"Expected Value of Perfect Information – {perspective.replace('_', ' ').title()} Perspective",
        xlabel="Willingness-to-Pay ($/QALY)",
        ylabel="EVPI ($ per person)",
        figsize=(10, 6)
    ) as (fig, ax):
        
        # Main EVPI curve
        ax.plot(evpi_df_plot['lambda'], evpi_df_plot['evpi'], 
               color='#1f77b4', linewidth=3.0, label='EVPI per person')
        
        # Fill area under curve
        ax.fill_between(evpi_df_plot['lambda'], 0, evpi_df_plot['evpi'], 
                       alpha=0.3, color='#1f77b4')
        
        # Add secondary y-axis for population EVPI
        ax2 = ax.twinx()
        ax2.plot(evpi_df_plot['lambda'], evpi_df_plot['evpi_population'], 
                color='#d62728', linewidth=2.0, linestyle='--', alpha=0.7,
                label=f'Population EVPI (n={population_size:,})')
        
        # Formatting
        ax.set_ylim(0, ax.get_ylim()[1] * 1.05)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax2.set_ylabel('Population EVPI ($)', color='#d62728')
        
        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, 
                 bbox_to_anchor=(1.15, 1), loc='upper left')
        
        fig.tight_layout()
        filename = f"v2_evpi_individual_{perspective.lower()}"
        save_multiformat(fig, outdir, filename, formats=['png', 'pdf', 'svg'], dpi=300)

def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate EVPI from PSA data")
    parser.add_argument("--psa", type=Path, required=True, help="Path to PSA CSV file")
    parser.add_argument("--strategies-yaml", type=Path, required=True, help="Strategy config YAML")
    parser.add_argument("--perspective", choices=["health_system", "societal"], required=True)
    parser.add_argument("--lambda-min", type=float, default=0)
    parser.add_argument("--lambda-max", type=float, default=75000)
    parser.add_argument("--lambda-step", type=float, default=2500)
    parser.add_argument("--population-size", type=int, default=1000)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=12345)
    return parser.parse_args(argv)

def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    set_seed(args.seed)
    
    # Load data
    lambda_grid = np.arange(args.lambda_min, args.lambda_max + args.lambda_step, args.lambda_step)
    data = load_analysis_inputs(
        psa_path=args.psa,
        config_path=args.strategies_yaml,
        perspective=args.perspective,
        lambda_grid=lambda_grid
    )
    
    # Calculate EVPI
    evpi_df = calculate_evpi(data.table, data.config.strategies, lambda_grid)
    
    # Save results
    args.outdir.mkdir(parents=True, exist_ok=True)
    evpi_df.to_csv(args.outdir / "evpi_results.csv", index=False)
    
    # Create plot
    plot_evpi(evpi_df, args.perspective, args.outdir, args.population_size)
    
    print(f"EVPI analysis saved to {args.outdir}")

if __name__ == "__main__":
    main()