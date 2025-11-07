#!/usr/bin/env python3
"""
Generate cost-effectiveness frontier plots for step-care pathways.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def create_frontier_plot(results_path, output_path):
    """Create cost-effectiveness frontier plot for step-care sequences."""

    # Load results
    results_df = pd.read_csv(results_path, index_col=0)

    # Parse ICERs from string format
    results_df['icers'] = results_df['icers'].apply(lambda x: eval(x) if isinstance(x, str) else x)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot individual strategies (mock data for demonstration)
    strategies = [
        ('Usual care', 1000, 2.0),
        ('rTMS', 8000, 2.15),
        ('PO-KA', 2000, 2.2),
        ('IV-KA', 5000, 2.3),
        ('ECT', 8000, 2.5)
    ]

    for name, cost, effect in strategies:
        ax.scatter(cost, effect, s=100, alpha=0.7, label=name)

    # Plot step-care sequences
    colors = ['red', 'blue']
    for i, (seq_name, row) in enumerate(results_df.iterrows()):
        ax.scatter(row['cost'], row['effect'], s=150, marker='s',
                  color=colors[i], label=seq_name, edgecolors='black', linewidth=2)

        # Add ICER annotations
        icers = row['icers']
        if icers:
            icer_text = f"ICERs: {[f'{icer:,.0f}' if icer != float('inf') else 'Dom' for icer in icers]}"
            ax.annotate(icer_text, (row['cost'], row['effect']),
                       xytext=(10, 10), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    ax.set_xlabel('Cost (AUD)', fontsize=12)
    ax.set_ylabel('Effectiveness (QALYs)', fontsize=12)
    ax.set_title('Cost-Effectiveness Frontier: Step-Care Pathways', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    # Add frontier line (simplified)
    frontier_points = [
        (1000, 2.0),   # Usual care
        (2000, 2.2),   # PO-KA
        (5000, 2.3),   # IV-KA
        (8000, 2.5)    # ECT
    ]
    frontier_costs, frontier_effects = zip(*frontier_points)
    ax.plot(frontier_costs, frontier_effects, 'k--', alpha=0.7, label='Efficiency Frontier')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Frontier plot saved to {output_path}")

def main():
    results_path = Path(__file__).parent.parent / "results" / "step_care_analysis.csv"
    output_path = Path(__file__).parent.parent / "figures" / "step_care_frontier.png"

    output_path.parent.mkdir(exist_ok=True)
    create_frontier_plot(results_path, output_path)

if __name__ == "__main__":
    main()