"""
Cost-Effectiveness Analysis Plotting

Publication-quality plots for CEA results.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.plotting.publication import (
    figure_context, save_multiformat, add_reference_line,
    format_axis_currency, format_axis_percentage, add_wtp_threshold,
    create_legend, JournalStandards
)
from analysis.plotting.publication import format_axis_wtp

__all__ = [
    "plot_ce_plane",
    "plot_ceac",
    "plot_ceaf",
    "plot_inmb_distribution",
    "plot_tornado",
]


def plot_ce_plane(
    costs: pd.DataFrame,
    effects: pd.DataFrame,
    reference_strategy: str,
    output_path: Path,
    wtp: float = 50000,
    currency: str = 'A$',
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
    legend_below: bool = False,
    ylim: Optional[Tuple[float, float]] = None,
) -> Path:
    """
    Create cost-effectiveness plane.
    
    Args:
        costs: DataFrame with strategies as columns, draws as rows
        effects: DataFrame with strategies as columns, draws as rows
        reference_strategy: Reference strategy name
        output_path: Output file path
        wtp: Willingness-to-pay threshold
        currency: Currency symbol
        title: Optional custom title
        standards: Journal standards
        legend_below: If True, place legend below plot instead of to the right
        ylim: Optional tuple of (ymin, ymax) for y-axis limits
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Cost-Effectiveness Plane:\nIncremental Costs and QALYs for Ketamine vs ECT Therapies"
    
    # Calculate incremental costs and effects
    inc_costs = costs.subtract(costs[reference_strategy], axis=0)
    inc_effects = effects.subtract(effects[reference_strategy], axis=0)
    
    with figure_context(
        title=title,
        xlabel="Incremental Quality-Adjusted Life Years (QALYs)",
        ylabel=f"Incremental Cost ({currency})",
        standards=standards
    ) as (fig, ax):
        
        # Plot each strategy
        for strategy in inc_costs.columns:
            if strategy == reference_strategy:
                continue

            ax.scatter(
                inc_effects.loc[:, strategy],
                inc_costs.loc[:, strategy],
                alpha=0.3,
                s=10,
                label=strategy
            )
        
        # Add reference lines
        add_reference_line(ax, 0, 'horizontal', color='gray', alpha=0.5)
        add_reference_line(ax, 0, 'vertical', color='gray', alpha=0.5)
        
        # Add WTP threshold
        add_wtp_threshold(ax, wtp, currency)
        
        # Format axes
        format_axis_currency(ax, 'y', currency)
        
        # Add legend (position based on legend_below parameter)
        if legend_below:
            # Place legend below the plot
            ax.legend(
                loc='upper center',
                bbox_to_anchor=(0.5, -0.15),
                ncol=3,
                frameon=True,
                fancybox=False,
                shadow=False
            )
        else:
            # Default: place legend to the right
            create_legend(ax, location='upper left')
        
        # Apply tight layout first to calculate optimal spacing
        fig.tight_layout()
        
        # Set y-axis limits if specified
        if ylim is not None:
            ax.set_ylim(ylim[0], ylim[1])
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_ceac(
    ceac_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create cost-effectiveness acceptability curve.
    
    Args:
        ceac_data: DataFrame with WTP thresholds as index, strategies as columns
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Cost-Effectiveness Acceptability Curves:\nKetamine vs Electroconvulsive Therapy for Treatment-Resistant Depression"
    
    with figure_context(
        title=title,
        xlabel=f"Willingness-to-Pay Threshold ({currency}/QALY)",
        ylabel="Probability of Being Cost-Effective",
        standards=standards
    ) as (fig, ax):
        
        # Plot each strategy
        for strategy in ceac_data.columns:
            ax.plot(
                ceac_data.index,
                ceac_data[strategy] * 100,  # Convert proportion to percentage
                label=strategy,
                linewidth=2
            )
        
        # Format axes: WTP x-axis displayed with currency symbol and thousands
        format_axis_wtp(ax, currency=currency, thousands=True)
        format_axis_percentage(ax, 'y', decimals=0)
        
        # Set y-axis limits
        ax.set_ylim(0, 100)
        
        # Add legend
        create_legend(ax, location='best')
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_ceaf(
    ceaf_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
    ceac_data: Optional[pd.DataFrame] = None,
    all_strategies: Optional[list] = None,
) -> Path:
    """
    Create cost-effectiveness acceptability frontier.

    Includes all strategies from CEAC data in legend, even if never optimal.

    Args:
        ceaf_data: DataFrame with WTP thresholds as index, optimal strategy as values
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
        ceac_data: Optional CEAC data with all strategies (for complete legend)
        all_strategies: Optional explicit list of all strategies to include

    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Cost-Effectiveness Acceptability Frontier:\nOptimal Treatment Strategies by Willingness-to-Pay Threshold"

    # Get strategies from CEAF (those that are optimal at some WTP)
    ceaf_strategies = list(ceaf_data['optimal_strategy'].unique())

    # Determine complete strategy list
    if all_strategies is not None:
        complete_strategies = all_strategies
    elif ceac_data is not None and 'strategy' in ceac_data.columns:
        complete_strategies = sorted(ceac_data['strategy'].unique())
    else:
        complete_strategies = ceaf_strategies.copy()

    # Ensure all CEAF strategies are in the complete list
    for s in ceaf_strategies:
        if s not in complete_strategies:
            complete_strategies.append(s)

    # Assign colors using a larger colormap if needed
    n_strategies = len(complete_strategies)
    from analysis.plotting.publication import _get_cmap
    cmap_name = 'tab10' if n_strategies <= 10 else 'Set3'
    cmap = _get_cmap(cmap_name)
    sampled_colors = cmap(np.linspace(0, 1, max(n_strategies, 10)))
    colors = [tuple(sampled_colors[i % len(sampled_colors)]) for i in range(n_strategies)]
    color_map = dict(zip(complete_strategies, colors))

    with figure_context(
        title=title,
        xlabel=f"Willingness-to-Pay Threshold ({currency}/QALY)",
        ylabel="Probability Cost-Effective",
        figsize=(10, 6),  # Increased size for more strategies
        standards=standards
    ) as (fig, ax):

        # First, plot transparent lines for ALL strategies from CEAC data (background)
        if ceac_data is not None and 'strategy' in ceac_data.columns:
            for strategy in complete_strategies:
                strategy_data = ceac_data[ceac_data['strategy'] == strategy].copy()
                if not strategy_data.empty:
                    wtp_col = 'lambda' if 'lambda' in strategy_data.columns else 'wtp'
                    prob_col = 'probability_optimal' if 'probability_optimal' in strategy_data.columns else strategy_data.columns[-1]
                    strategy_data = strategy_data.sort_values(wtp_col)
                    ax.plot(
                        strategy_data[wtp_col],
                        strategy_data[prob_col] * 100,
                        color=color_map[strategy],
                        alpha=0.3,
                        linewidth=1.5,
                        linestyle='--',
                        zorder=1,
                        label=f'{strategy} (CEAC)'
                    )

        # Then create stacked area plot for CEAF frontier (foreground)
        wtp_col_ceaf = 'lambda' if 'lambda' in ceaf_data.columns else 'wtp'
        if wtp_col_ceaf in ceaf_data.columns:
            wtp_values = ceaf_data[wtp_col_ceaf].values
        else:
            wtp_values = ceaf_data.index.values

        # Plot strategies that are optimal at some WTP (filled areas)
        for strategy in ceaf_strategies:
            mask = ceaf_data['optimal_strategy'] == strategy
            # Get probability values - handle different column names
            prob_col = 'probability' if 'probability' in ceaf_data.columns else 'ceaf_probability'
            prob_series = ceaf_data.loc[mask, prob_col].astype(float)
            if wtp_col_ceaf in ceaf_data.columns:
                wtp_subset = ceaf_data.loc[mask, wtp_col_ceaf].values
            else:
                wtp_subset = wtp_values[mask]

            if len(wtp_subset) > 0:
                ax.fill_between(
                    wtp_subset,
                    0,
                    prob_series.values * 100,
                    alpha=0.7,
                    color=color_map[strategy],
                    label=f'{strategy} (CEAF)',
                    zorder=2
                )

        # Add legend entries for strategies not in CEAF (never optimal)
        for strategy in complete_strategies:
            if strategy not in ceaf_strategies:
                ax.plot([], [], '--', c=color_map[strategy], linewidth=1.5,
                       label=f'{strategy} (never optimal)', alpha=0.5)

        # Format axes (WTP on x-axis)
        format_axis_wtp(ax, currency=currency, thousands=True)
        format_axis_percentage(ax, 'y', decimals=0)

        # Set y-axis limits
        ax.set_ylim(0, 100)

        # Add legend with better positioning for many strategies
        if n_strategies > 6:
            # Place legend below the plot for many strategies
            create_legend(ax, location='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
        else:
            create_legend(ax, location='best')

        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)

    return artifacts.base_path


def plot_inmb_distribution(
    inmb_data: pd.DataFrame,
    output_path: Path,
    wtp: float = 50000,
    currency: str = 'A$',
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create incremental net monetary benefit distribution plot.
    
    Args:
        inmb_data: DataFrame with strategies as columns, draws as rows
        output_path: Output file path
        wtp: Willingness-to-pay threshold
        currency: Currency symbol
        title: Optional custom title
        standards: Journal standards
        legend_below: If True, place legend below plot instead of to the right
        ylim: Optional tuple of (ymin, ymax) for y-axis limits
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = f"Incremental Net Monetary Benefit Distribution:\nKetamine vs ECT Therapies\n(WTP = {currency}{wtp:,.0f}/QALY)"
    
    with figure_context(
        title=title,
        xlabel=f"Incremental Net Monetary Benefit ({currency})",
        ylabel="Density",
        standards=standards
    ) as (fig, ax):
        
        # Plot distribution for each strategy
        for strategy in inmb_data.columns:
            ax.hist(
                inmb_data[strategy],
                bins=50,
                alpha=0.5,
                density=True,
                label=strategy
            )
        
        # Add reference line at zero
        add_reference_line(ax, 0, 'vertical', label='Break-even')
        
        # Format axes
        format_axis_currency(ax, 'x', currency)
        
        # Add legend
        create_legend(ax, location='best')
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_tornado(
    tornado_data: pd.DataFrame,
    output_path: Path,
    outcome_label: str = "ICER",
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create tornado diagram for sensitivity analysis.
    
    Args:
        tornado_data: DataFrame with parameters, low/high values
        output_path: Output file path
        outcome_label: Label for outcome measure
        title: Optional custom title
        standards: Journal standards
        legend_below: If True, place legend below plot instead of to the right
        ylim: Optional tuple of (ymin, ymax) for y-axis limits
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Tornado Diagram - One-Way Sensitivity Analysis"
    
    # Sort by impact (high - low)
    tornado_data = tornado_data.copy()
    tornado_data['impact'] = abs(tornado_data['high'] - tornado_data['low'])
    tornado_data = tornado_data.sort_values('impact', ascending=True)
    
    with figure_context(
        title=title,
        xlabel=outcome_label,
        ylabel="Parameter",
        figsize=(8, max(6, len(tornado_data) * 0.3)),
        standards=standards
    ) as (fig, ax):
        
        # Create horizontal bars
        y_pos = np.arange(len(tornado_data))
        
        for i, (idx, row) in enumerate(tornado_data.iterrows()):
            low = row['low']
            high = row['high']
            base = row.get('base', (low + high) / 2)
            
            # Draw bar from low to high
            ax.barh(
                i,
                high - low,
                left=low,
                height=0.8,
                alpha=0.7,
                color='steelblue'
            )
            
            # Mark base case
            ax.plot(base, i, 'ko', markersize=4)
        
        # Set y-axis labels
        ax.set_yticks(y_pos)
        ax.set_yticklabels(tornado_data.index, fontsize=8)
        
        # Add reference line at base case
        if 'base' in tornado_data.columns:
            base_value = tornado_data['base'].iloc[0]
            add_reference_line(ax, base_value, 'vertical', label='Base case')
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path
