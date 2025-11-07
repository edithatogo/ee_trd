"""
Value-Based Pricing Visualization

Publication-quality plots for value-based pricing analysis.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.plotting.publication import (
    figure_context,
    save_multiformat,
    format_axis_currency,
    format_axis_percentage,
    create_legend,
)
from analysis.plotting.publication import format_axis_wtp
from matplotlib.ticker import FuncFormatter


def plot_vbp_curve(
    vbp_data: pd.DataFrame,
    output_path: Path,
    wtp_threshold: float = 50000,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot value-based pricing curve showing price vs probability of cost-effectiveness.
    
    Args:
        vbp_data: DataFrame with columns ['price', 'prob_ce', 'strategy']
        output_path: Output file path
        wtp_threshold: Willingness-to-pay threshold
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = f'Value-Based Pricing Curve: Ketamine vs Electroconvulsive Therapy (WTP = {currency}{wtp_threshold:,.0f}/QALY)'
    
    with figure_context(
        title=title,
        xlabel=f'Price per Treatment ({currency})',
        ylabel='Probability Cost-Effective'
    ) as (fig, ax):
        
        # Plot VBP curve for each strategy
        for strategy in vbp_data['therapy'].unique() if 'therapy' in vbp_data.columns else vbp_data['strategy'].unique():
            strategy_col = 'therapy' if 'therapy' in vbp_data.columns else 'strategy'
            strategy_data = vbp_data[vbp_data[strategy_col] == strategy]
            
            # Handle different column names
            price_col = 'threshold_price' if 'threshold_price' in strategy_data.columns else 'price'
            prob_col = 'probability_ce' if 'probability_ce' in strategy_data.columns else 'prob_ce'
            
            ax.plot(
                strategy_data[price_col],
                strategy_data[prob_col],
                label=strategy,
                linewidth=2,
                marker='o',
                markersize=4
            )
        
        # Add reference lines
        ax.axhline(y=0.5, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='50% threshold')
        ax.axhline(y=0.95, color='gray', linestyle=':', linewidth=1, alpha=0.5, label='95% threshold')
        
        # Formatting
        format_axis_currency(ax, axis='x', currency=currency)
        format_axis_percentage(ax, axis='y')
        
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        create_legend(ax, loc='best')
        
        return save_multiformat(fig, output_path)


def plot_threshold_price(
    threshold_data: pd.DataFrame,
    output_path: Path,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot threshold prices at different WTP thresholds.
    
    Args:
        threshold_data: DataFrame with columns ['wtp_threshold', 'threshold_price', 'strategy']
        output_path: Output file path
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Threshold Prices at Different WTP Levels: Ketamine vs Electroconvulsive Therapy'
    
    # Handle different column names
    strategy_col = 'therapy' if 'therapy' in threshold_data.columns else 'strategy'
    wtp_col = 'wtp' if 'wtp' in threshold_data.columns else ('wtp_threshold' if 'wtp_threshold' in threshold_data.columns else 'lambda')
    
    with figure_context(
        title=title,
        xlabel='Willingness-to-Pay Threshold (per QALY)',
        ylabel=f'Threshold Price ({currency})'
    ) as (fig, ax):
        
        # Plot threshold price for each strategy
        strategies = threshold_data[strategy_col].unique()
        x = np.arange(len(threshold_data[wtp_col].unique()))
        width = 0.8 / len(strategies)
        
        for i, strategy in enumerate(strategies):
            strategy_data = threshold_data[threshold_data[strategy_col] == strategy]
            offset = (i - len(strategies)/2 + 0.5) * width
            ax.bar(
                x + offset,
                strategy_data['threshold_price'],
                width,
                label=strategy,
                alpha=0.8
            )
        
        # Formatting
        ax.set_xticks(x)
        # X-axis represents WTP thresholds; use WTP formatter for clear currency ticks
        format_axis_wtp(ax, currency=currency, thousands=True)
        format_axis_currency(ax, axis='y', currency=currency)

        ax.grid(True, alpha=0.3, linestyle='--', axis='y')

        create_legend(ax, loc='best')

        return save_multiformat(fig, output_path)


def plot_price_elasticity(
    elasticity_data: pd.DataFrame,
    output_path: Path,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot price elasticity of demand.
    
    Args:
        elasticity_data: DataFrame with columns ['price', 'demand', 'strategy']
        output_path: Output file path
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Price Elasticity of Demand: Ketamine vs Electroconvulsive Therapy'
    
    # Handle different column names
    strategy_col = 'therapy' if 'therapy' in elasticity_data.columns else 'strategy'
    demand_col = 'probability_ce' if 'probability_ce' in elasticity_data.columns else 'demand'
    
    with figure_context(
        title=title,
        xlabel=f'Price per Treatment ({currency})',
        ylabel='Relative Demand'
    ) as (fig, ax):
        
        # Plot elasticity curve for each strategy
        for strategy in elasticity_data[strategy_col].unique():
            strategy_data = elasticity_data[elasticity_data[strategy_col] == strategy]
            ax.plot(
                strategy_data['price'],
                strategy_data[demand_col],
                label=strategy,
                linewidth=2,
                marker='s',
                markersize=4
            )
        
        # Formatting
        format_axis_currency(ax, axis='x', currency=currency)
        
        ax.grid(True, alpha=0.3, linestyle='--')
        
        create_legend(ax, loc='best')
        
        return save_multiformat(fig, output_path)


def plot_multi_indication_vbp(
    indication_data: pd.DataFrame,
    output_path: Path,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot value-based pricing across multiple indications.
    
    Args:
        indication_data: DataFrame with columns ['indication', 'threshold_price', 'strategy']
        output_path: Output file path
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Value-Based Pricing Across Indications: Ketamine vs Electroconvulsive Therapy'
    
    # Handle different column names
    strategy_col = 'therapy' if 'therapy' in indication_data.columns else 'strategy'
    
    with figure_context(
        title=title,
        xlabel='Indication',
        ylabel=f'Threshold Price ({currency})',
        figsize=(12, 6)
    ) as (fig, ax):
        
        # Plot threshold prices by indication
        strategies = indication_data[strategy_col].unique()
        indications = indication_data['indication'].unique()
        x = np.arange(len(indications))
        width = 0.8 / len(strategies)
        
        for i, strategy in enumerate(strategies):
            strategy_data = indication_data[indication_data[strategy_col] == strategy]
            offset = (i - len(strategies)/2 + 0.5) * width
            ax.bar(
                x + offset,
                strategy_data['threshold_price'],
                width,
                label=strategy,
                alpha=0.8
            )
        
        # Formatting
        ax.set_xticks(x)
        ax.set_xticklabels(indications, rotation=45, ha='right')
        format_axis_currency(ax, axis='y', currency=currency)
        
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        create_legend(ax, loc='best')
        
        return save_multiformat(fig, output_path)


def plot_risk_sharing_scenarios(
    scenario_data: pd.DataFrame,
    output_path: Path,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot risk-sharing agreement scenarios.
    
    Args:
        scenario_data: DataFrame with columns ['scenario', 'expected_cost', 'expected_qaly', 'strategy']
        output_path: Output file path
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Risk-Sharing Agreement Scenarios: Ketamine vs Electroconvulsive Therapy'
    
    # Handle different column names
    strategy_col = 'therapy' if 'therapy' in scenario_data.columns else 'strategy'
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    strategies = scenario_data[strategy_col].unique()
    scenarios = scenario_data['scenario'].unique()
    x = np.arange(len(scenarios))
    width = 0.8 / len(strategies)
    
    # Plot top panel: prefer explicit 'price_reduction', otherwise try engine 'value'
    for i, strategy in enumerate(strategies):
        strategy_data = scenario_data[scenario_data[strategy_col] == strategy]
        offset = (i - len(strategies)/2 + 0.5) * width

        # Prefer explicit price_reduction column
        if 'price_reduction' in strategy_data.columns:
            values = np.asarray(strategy_data['price_reduction'].values, dtype=float)
        # Engine fallback: many engines return a 'value' column describing the risk metric
        elif 'value' in strategy_data.columns:
            values = np.asarray(strategy_data['value'].values, dtype=float)
        else:
            # Last resort: attempt expected_cost or zeros
            values = np.asarray(strategy_data.get('expected_cost', [0] * len(strategy_data)), dtype=float)

        ax1.bar(
            x + offset,
            values,
            width,
            label=strategy,
            alpha=0.8
        )
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios, rotation=45, ha='right')

    # Determine the nature of top-panel metrics to choose axis label and formatting
    top_metrics = list(scenario_data['risk_metric'].dropna().unique()) if 'risk_metric' in scenario_data.columns else []
    top_metrics_lower = [m.lower() for m in top_metrics]
    # Heuristic: treat explicit price/threshold/price_reduction metrics as monetary
    monetary_keywords = ('price', 'price_reduction', 'threshold')
    top_is_monetary = all(any(k in m for k in monetary_keywords) for m in top_metrics_lower) if top_metrics_lower else False

    if top_is_monetary:
        # Use currency formatter for monetary metrics
        ax1.set_ylabel('Price reduction', fontsize=12, fontweight='bold')
        format_axis_currency(ax1, axis='y', currency=currency)
    else:
        # Use human-readable label for a single known metric, otherwise generic label
        if len(top_metrics) == 1:
            pretty = top_metrics[0].replace('_', ' ').title()
            ax1.set_ylabel(pretty, fontsize=12, fontweight='bold')
        else:
            ax1.set_ylabel('Value (heterogeneous units)', fontsize=12, fontweight='bold')
            # Add small note that units vary by scenario/metric
            fig.text(0.99, 0.01, 'Note: top-panel values may have different units by scenario (see description column).',
                     ha='right', va='bottom', fontsize=8, alpha=0.7)

        # Use thousands separator formatting without currency prefix to avoid misleading labels
        ax1.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:,.0f}" if abs(v) >= 1 else f"{v:.3f}"))

    ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
    create_legend(ax1, loc='best')
    
    # Plot probability CE
    for i, strategy in enumerate(strategies):
        strategy_data = scenario_data[scenario_data[strategy_col] == strategy]
        offset = (i - len(strategies)/2 + 0.5) * width
        
        # Bottom panel: probability-like plot. Prefer explicit probability_ce.
        if 'probability_ce' in strategy_data.columns:
            values = np.asarray(strategy_data['probability_ce'].values, dtype=float)
        elif 'value' in strategy_data.columns:
            # Use raw 'value' for bottom panel (do not normalize monetary values). If the
            # intended metric is a probability, the engine should provide 'probability_ce'.
            values = np.asarray(strategy_data['value'].values, dtype=float)
        else:
            values = np.asarray(strategy_data.get('expected_qaly', [0] * len(strategy_data)), dtype=float)

        ax2.bar(
            x + offset,
            values,
            width,
            label=strategy,
            alpha=0.8
        )
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios, rotation=45, ha='right')
    ax2.set_xlabel('Risk-Sharing Scenario', fontsize=12, fontweight='bold')

    # Determine bottom panel label/format
    if 'probability_ce' in scenario_data.columns:
        ax2.set_ylabel('Probability Cost-Effective', fontsize=12, fontweight='bold')
        format_axis_percentage(ax2, axis='y')
        ax2.set_ylim(0, 1)
    else:
        # If a single bottom metric exists, use it for labeling; otherwise generic
        bottom_metrics = list(scenario_data['risk_metric'].dropna().unique()) if 'risk_metric' in scenario_data.columns else []
        if len(bottom_metrics) == 1:
            az = bottom_metrics[0].replace('_', ' ').title()
            ax2.set_ylabel(az, fontsize=12, fontweight='bold')
        else:
            ax2.set_ylabel('Value', fontsize=12, fontweight='bold')

        ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:,.0f}" if abs(v) >= 1 else f"{v:.3f}"))
        ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    return save_multiformat(fig, output_path)
