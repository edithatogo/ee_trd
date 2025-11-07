"""
Advanced Visualization Module for Health Economic Evaluation

This module provides publication-ready graphics and advanced visualization capabilities
for health economic models.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path


def configure_publication_style():
    """Configure matplotlib for publication-quality graphics."""
    plt.style.use('seaborn-v0_8-colorblind')  # More accessible color scheme
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'figure.titlesize': 16,
        'figure.figsize': (10, 6),
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,
        'lines.linewidth': 2,
        'patch.linewidth': 0.5,
        'grid.alpha': 0.3,
        'axes.spines.top': False,
        'axes.spines.right': False
    })


def create_cost_effectiveness_plane(
    costs, 
    effects, 
    strategies, 
    wtp_threshold=50000, 
    title="Cost-Effectiveness Plane",
    filename=None
):
    """Create a publication-ready cost-effectiveness plane."""
    configure_publication_style()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Reference strategy is typically first in the list (e.g., standard of care)
    ref_cost = costs[0]
    ref_effect = effects[0]
    
    # Calculate incremental values
    inc_costs = np.array(costs) - ref_cost
    inc_effects = np.array(effects) - ref_effect
    
    # Define quadrants
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.7)
    
    # Plot strategies
    colors = plt.cm.tab10(np.linspace(0, 1, len(strategies)))
    for i, (inc_c, inc_e, strategy, color) in enumerate(zip(inc_costs, inc_effects, strategies, colors)):
        ax.scatter(inc_e, inc_c, s=100, color=color, alpha=0.7, edgecolors='black', linewidth=1)
        ax.annotate(strategy, (inc_e, inc_c), xytext=(5, 5), textcoords='offset points', fontsize=10)
    
    # Add willingness-to-pay threshold line
    x_limit = ax.get_xlim()[1]
    y_wtp = wtp_threshold * np.array(ax.get_xlim())
    ax.plot(ax.get_xlim(), y_wtp, color='red', linestyle='--', alpha=0.8, label=f'WTP = ${wtp_threshold:,}/QALY')
    
    ax.set_xlabel('Incremental Effect (QALYs)')
    ax.set_ylabel('Incremental Cost ($AUD)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    return fig, ax


def create_ceac(
    prob_ce, 
    strategies, 
    wtp_values,
    title="Cost-Effectiveness Acceptability Curve",
    filename=None
):
    """Create publication-ready cost-effectiveness acceptability curve."""
    configure_publication_style()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i, (strategy, probs) in enumerate(zip(strategies, prob_ce)):
        ax.plot(wtp_values, probs, label=strategy, linewidth=2.5)
    
    ax.set_xlabel('Willingness-to-Pay Threshold ($/QALY)')
    ax.set_ylabel('Probability of Cost-Effectiveness')
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    return fig, ax


def create_tornado_diagram(
    base_value,
    parameter_changes,
    parameter_names,
    title="Tornado Diagram: One-Way Sensitivity Analysis",
    filename=None
):
    """Create a publication-ready tornado diagram."""
    configure_publication_style()
    
    fig, ax = plt.subplots(figsize=(10, len(parameter_names)*0.4 + 2))
    
    # Calculate changes from base case
    changes = [val - base_value for val in parameter_changes]
    indices = np.arange(len(parameter_names))
    
    # Sort by absolute impact
    sorted_indices = sorted(indices, key=lambda i: abs(changes[i]), reverse=True)
    sorted_names = [parameter_names[i] for i in sorted_indices]
    sorted_changes = [changes[i] for i in sorted_indices]
    
    # Create horizontal bar chart
    ax.barh(range(len(sorted_names)), sorted_changes, color='skyblue', alpha=0.7)
    
    # Add base value line
    ax.axvline(x=0, color='black', linestyle='-', alpha=0.7)
    ax.axvline(x=base_value, color='red', linestyle='--', alpha=0.7, label=f'Base Case = {base_value:.2f}')
    
    ax.set_yticks(range(len(sorted_names)))
    ax.set_yticklabels(sorted_names)
    ax.set_xlabel('Change in Outcome')
    ax.set_title(title)
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    
    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    return fig, ax


def create_probabilistic_sensitivity_analysis_visual(
    ce_plane_data,
    n_simulations=1000,
    title="Probabilistic Sensitivity Analysis - Cost-Effectiveness Plane",
    filename=None
):
    """Create a publication-ready scatter plot for PSA results."""
    configure_publication_style()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Extract data
    costs = ce_plane_data['cost']
    effects = ce_plane_data['effect']
    strategies = ce_plane_data['strategy']
    
    # Plot scatter
    unique_strategies = ce_plane_data['strategy'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_strategies)))
    
    for i, strategy in enumerate(unique_strategies):
        strat_data = ce_plane_data[ce_plane_data['strategy'] == strategy]
        ax.scatter(
            strat_data['effect'], 
            strat_data['cost'], 
            s=20, 
            alpha=0.6, 
            label=strategy, 
            color=colors[i]
        )
    
    ax.set_xlabel('Effectiveness (QALYs)')
    ax.set_ylabel('Costs ($AUD)')
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    return fig, ax


def create_value_of_information_visual(
    evpi_data,
    wtp_values,
    title="Expected Value of Perfect Information",
    filename=None
):
    """Create a publication-ready EVPI curve."""
    configure_publication_style()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(wtp_values, evpi_data, color='purple', linewidth=2.5, label='EVPI')
    ax.fill_between(wtp_values, 0, evpi_data, color='purple', alpha=0.3)
    
    ax.set_xlabel('Willingness-to-Pay Threshold ($/QALY)')
    ax.set_ylabel('Expected Value of Perfect Information ($AUD)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    return fig, ax


def finalize_figure_for_publication(fig, ax, caption="", journal_format="generic"):
    """Standardize figure formatting for publication."""
    # Common formatting
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Journal-specific formatting if applicable
    if journal_format == "jama":
        # JAMA specific formatting
        plt.rcParams.update({
            'font.family': 'Times New Roman',
            'axes.linewidth': 0.8,
            'grid.linewidth': 0.5
        })
    elif journal_format == "lancet":
        # Lancet specific formatting
        plt.rcParams.update({
            'font.family': 'Arial',
            'axes.linewidth': 1.2,
            'lines.linewidth': 2.5
        })
    
    # Add caption if provided
    if caption:
        fig.text(0.5, 0.02, caption, ha='center', fontsize=10, style='italic')
    
    return fig, ax