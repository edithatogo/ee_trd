#!/usr/bin/env python3
"""
Cost-Effectiveness Planes for Psychedelic Therapies vs ECT
- Scatter plots of incremental costs vs incremental QALYs
- Shows uncertainty from PSA results
- Includes WTP threshold lines
- Outputs ce_plane_{strategy}_{country}.png
"""
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from trd_cea.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

def create_ce_plane(country="AU"):
    """Create cost-effectiveness plane for each strategy"""
    # Load PSA results
    psa_file = f"psa_results_{country}.csv"
    if not os.path.exists(psa_file):
        print(f"PSA results not found: {psa_file}")
        return

    psa_data = pd.read_csv(psa_file)

    # Define WTP thresholds for reference lines
    wtp_thresholds = [0, 25000, 50000, 75000, 100000]

    strategies = ['Ketamine', 'Esketamine', 'Psilocybin']

    for strategy in strategies:
        print(f"Creating CE plane for {strategy} in {country}")

        # Filter data for this strategy
        strat_data = psa_data[psa_data['strategy'] == strategy]

        # Create the CE plane
        plt.figure(figsize=(12, 10))

        # Plot the scatter points
        plt.scatter(strat_data['inc_qalys'], strat_data['inc_cost'],
                   alpha=0.6, s=30, color='blue', edgecolors='black', linewidth=0.5)

        # Add WTP threshold lines
        qaly_range = np.linspace(strat_data['inc_qalys'].min(), strat_data['inc_qalys'].max(), 100)

        colors = ['red', 'orange', 'green', 'purple', 'brown']
        for i, wtp in enumerate(wtp_thresholds):
            cost_threshold = wtp * qaly_range
            plt.plot(qaly_range, cost_threshold, color=colors[i], linestyle='--',
                    linewidth=2, label=f'WTP = ${wtp:,} per QALY', alpha=0.8)

        # Add reference lines
        plt.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        plt.axvline(x=0, color='black', linestyle='-', linewidth=1, alpha=0.5)

        # Shade quadrants
        # Southwest quadrant (cost-saving, QALYs lost) - dominated
        plt.fill_betweenx([-50000, 0], strat_data['inc_qalys'].min(), 0,
                         color='red', alpha=0.1, label='Dominated')
        # Southeast quadrant (cost-saving, QALYs gained) - dominant
        plt.fill_betweenx([0, 50000], 0, strat_data['inc_qalys'].max(),
                         color='green', alpha=0.1, label='Dominant')

        # Add labels and title
        plt.xlabel('Incremental QALYs')
        plt.ylabel('Incremental Cost ($)')
        plt.title(f'Cost-Effectiveness Plane: {strategy} vs ECT\n{country}\n'
                 f'PSA Results (n={len(strat_data)} simulations)')

        # Add statistics text
        _mean_qaly = strat_data['inc_qalys'].mean()
        _mean_cost = strat_data['inc_cost'].mean()
        _prob_ce_50k = (strat_data['nmb'] > 0).mean()

        stats_text = '.1f'
        plt.figtext(0.02, 0.02, stats_text, fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

        # Set axis limits with some padding
        qaly_padding = (strat_data['inc_qalys'].max() - strat_data['inc_qalys'].min()) * 0.1
        cost_padding = (strat_data['inc_cost'].max() - strat_data['inc_cost'].min()) * 0.1

        plt.xlim(strat_data['inc_qalys'].min() - qaly_padding,
                strat_data['inc_qalys'].max() + qaly_padding)
        plt.ylim(strat_data['inc_cost'].min() - cost_padding,
                strat_data['inc_cost'].max() + cost_padding)

        # Format axis labels
        plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda x, p: '.2f'))
        plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, p: '${:,.0f}'.format(x)))

        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()
        plt.savefig(f'ce_plane_{strategy.lower()}_{country}.png', dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  Saved ce_plane_{strategy.lower()}_{country}.png")

def create_combined_ce_plane(country="AU"):
    """Create a combined CE plane showing all strategies"""
    # Load PSA results
    psa_file = f"psa_results_{country}.csv"
    if not os.path.exists(psa_file):
        print(f"PSA results not found: {psa_file}")
        return

    psa_data = pd.read_csv(psa_file)

    plt.figure(figsize=(14, 10))

    strategies = ['Ketamine', 'Esketamine', 'Psilocybin']
    colors = ['blue', 'red', 'green']
    markers = ['o', 's', '^']

    for i, strategy in enumerate(strategies):
        strat_data = psa_data[psa_data['strategy'] == strategy]
        plt.scatter(strat_data['inc_qalys'], strat_data['inc_cost'],
                   alpha=0.6, s=40, color=colors[i], marker=markers[i],
                   edgecolors='black', linewidth=0.5, label=strategy)

    # Add WTP threshold line (50k)
    qaly_range = np.linspace(psa_data['inc_qalys'].min(), psa_data['inc_qalys'].max(), 100)
    cost_threshold = 50000 * qaly_range
    plt.plot(qaly_range, cost_threshold, color='black', linestyle='--',
            linewidth=2, label='WTP = $50,000 per QALY')

    # Add reference lines
    plt.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    plt.axvline(x=0, color='black', linestyle='-', linewidth=1, alpha=0.5)

    plt.xlabel('Incremental QALYs')
    plt.ylabel('Incremental Cost ($)')
    plt.title(f'Cost-Effectiveness Plane: All Strategies vs ECT\n{country}')

    # Format axis labels
    plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda x, p: '.2f'))
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, p: '${:,.0f}'.format(x)))

    plt.grid(True, alpha=0.3)
    plt.legend()

    # Set axis limits
    plt.xlim(psa_data['inc_qalys'].min() * 1.1, psa_data['inc_qalys'].max() * 1.1)
    plt.ylim(psa_data['inc_cost'].min() * 1.1, psa_data['inc_cost'].max() * 1.1)

    plt.tight_layout()
    plt.savefig(f'ce_plane_combined_{country}.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved ce_plane_combined_{country}.png")

def main():
    for country in ["AU", "NZ"]:
        print(f"Creating cost-effectiveness planes for {country}")
        create_ce_plane(country)
        create_combined_ce_plane(country)
        print(f"Completed CE planes for {country}")

if __name__ == "__main__":
    main()
