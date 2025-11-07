#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import yaml
import pandas as pd

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis_core.plotting import (
    figure_context,
    save_figure_multiformat,
    write_figure_caption,
)
from analysis_core.export import write_manuscript_table
from utils import set_seed

def load_config(bia_config_path: Path) -> tuple[dict, dict]:
    with open(bia_config_path, 'r') as f:
        bia_config = yaml.safe_load(f)
    
    strategies_path = bia_config_path.parent / 'strategies.yml'
    with open(strategies_path, 'r') as f:
        strategies_config = yaml.safe_load(f)
    
    return bia_config, strategies_config

def compute_bia(bia_config: dict, strategies_config: dict) -> pd.DataFrame:
    years = bia_config['time_horizon_years']
    base = strategies_config.get('base', 'Usual care')
    
    # Get all therapies from market_share
    all_therapies = list(bia_config['market_share'].keys())
    if base not in all_therapies:
        all_therapies.append(base)
    
    # Ensure base has entries
    if base not in bia_config['uptake_by_year']:
        bia_config['uptake_by_year'][base] = {year: 1.0 for year in years}
    if base not in bia_config['market_share']:
        bia_config['market_share'][base] = 1.0 - sum(bia_config['market_share'].values())
    
    # Adjust uptakes if they don't sum to 1
    for year in years:
        total_uptake = sum(bia_config['uptake_by_year'].get(therapy, {}).get(year, 0) for therapy in all_therapies)
        if total_uptake < 1.0:
            bia_config['uptake_by_year'][base][year] = 1.0 - total_uptake
    
    results = []
    cumulative_cost = 0.0
    
    for year in years:
        pop = bia_config['population_by_year'][year]
        eligible = pop * bia_config['eligibility_rate']
        
        total_cost = 0.0
        base_cost = 0.0
        
        for therapy in all_therapies:
            uptake = bia_config['uptake_by_year'].get(therapy, {}).get(year, 0)
            market_share = bia_config['market_share'].get(therapy, 0)
            patients = eligible * uptake * market_share
            
            # Get costs
            costs = bia_config.get('per_patient_costs', {}).get(therapy, {})
            drug = costs.get('drug', strategies_config.get('prices', {}).get(therapy, 0))
            admin = costs.get('admin', 0)
            monitoring = costs.get('monitoring', 0)
            cost_per_patient = drug + admin + monitoring
            
            therapy_cost = patients * cost_per_patient
            total_cost += therapy_cost
            if therapy == base:
                base_cost = therapy_cost
        
        incremental_cost = total_cost - base_cost
        
        if bia_config.get('include_discounting', False):
            discount_rate = bia_config.get('discount_rate', 0.05)  # default if not specified
            discount_factor = 1 / (1 + discount_rate) ** (year - bia_config['price_year'])
            incremental_cost *= discount_factor
        
        cumulative_cost += incremental_cost
        pmpm = incremental_cost / (pop * 12) if pop > 0 else 0
        
        results.append({
            'year': year,
            'population': pop,
            'eligible_population': eligible,
            'incremental_cost': incremental_cost,
            'cumulative_cost': cumulative_cost,
            'pmpm': pmpm
        })
    
    return pd.DataFrame(results)

def save_results(df: pd.DataFrame, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    # Save to outdir for analysis
    df.to_csv(outdir / 'bia_annual.csv', index=False)
    df[['year', 'cumulative_cost']].to_csv(outdir / 'bia_cumulative.csv', index=False)
    # Save clean versions to tables_for_manuscript/
    write_manuscript_table(df, 'bia_annual.csv', index=False)
    write_manuscript_table(df[['year', 'cumulative_cost']], 'bia_cumulative.csv', index=False)

def plot_annual_incremental(df: pd.DataFrame, outdir: Path, config: dict) -> None:
    with figure_context("Annual Incremental Cost", xlabel="Year", ylabel="Incremental Cost") as (fig, ax):
        ax.plot(df['year'], df['incremental_cost'], marker='o', linestyle='-', color='blue')
        ax.grid(True)
        save_figure_multiformat(fig, outdir, 'bia_annual_incremental')

        write_figure_caption(
            outdir,
            'bia_annual_incremental',
            perspective=config['perspective'],
            comparator="Usual care",
            interpretation="Annual incremental cost of introducing oral ketamine compared to usual care over the time horizon. Costs are in 2025 AUD and include drug, administration, and monitoring expenses."
        )

def plot_cumulative(df: pd.DataFrame, outdir: Path, config: dict) -> None:
    with figure_context("Cumulative Incremental Cost", xlabel="Year", ylabel="Cumulative Cost") as (fig, ax):
        ax.plot(df['year'], df['cumulative_cost'], marker='o', linestyle='-', color='green')
        ax.fill_between(df['year'], df['cumulative_cost'], alpha=0.3, color='green')
        ax.grid(True)
        save_figure_multiformat(fig, outdir, 'bia_cumulative')

        write_figure_caption(
            outdir,
            'bia_cumulative',
            perspective=config['perspective'],
            comparator="Usual care",
            interpretation="Cumulative incremental cost of introducing oral ketamine compared to usual care. The shaded area represents the total budget impact over the time horizon."
        )

def write_methods_snippet(config: dict, outdir: Path) -> None:
    perspective = config['perspective']
    time_horizon = len(config['time_horizon_years'])
    eligibility = config['eligibility_rate']
    include_discounting = config.get('include_discounting', False)
    discount_rate = config.get('discount_rate', 0.05)

    snippet = f"""
# Budget Impact Analysis Methods

Budget impact analysis (BIA) was conducted from a {perspective} perspective over a {time_horizon}-year time horizon.

## Population and Eligibility
The analysis considered an eligible population defined as {eligibility * 100:.1f}% of the total population in each year. Population sizes by year were as specified in the configuration.

## Uptake and Market Share
Uptake rates for each therapy varied by year, with market shares allocated as follows: {config['market_share']}.

## Costs
Per-patient costs included drug price, administration, and monitoring costs. Drug prices were sourced from strategies.yml unless overridden. All costs were in {config['price_year']} {config['currency']} prices.

## Discounting
{f"Costs were discounted at a rate of {discount_rate:.1%} per year." if include_discounting else "No discounting was applied."}

This analysis follows ISPOR BIA guidelines, estimating the financial impact of adopting the new therapy.
"""
    (outdir / 'methods_snippet_bia.md').write_text(snippet.strip())

def run(bia_config: Path, outdir: Path, seed: int) -> None:
    set_seed(seed)
    bia_config_data, strategies_config = load_config(bia_config)
    df = compute_bia(bia_config_data, strategies_config)
    save_results(df, outdir)
    plot_annual_incremental(df, outdir, bia_config_data)
    plot_cumulative(df, outdir, bia_config_data)
    write_methods_snippet(bia_config_data, outdir)

def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Make Budget Impact Analysis (BIA) artifacts")
    p.add_argument("--bia-config", required=True, help="Path to BIA config YAML")
    p.add_argument("--outdir", required=True, help="Output directory for BIA artifacts")
    p.add_argument("--seed", type=int, default=12345, help="Random seed")
    return p.parse_args(argv)

def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    run(Path(args.bia_config), Path(args.outdir), args.seed)

if __name__ == "__main__":
    main()