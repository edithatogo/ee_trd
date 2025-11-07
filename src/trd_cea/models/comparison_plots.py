"""
Comparison and Dashboard Plotting

Multi-panel comparison visualizations and comprehensive dashboards.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd

from analysis.plotting.publication import (
    journal_style, save_multiformat, format_axis_currency,
    format_axis_percentage, format_axis_wtp, JournalStandards
)

__all__ = [
    "plot_perspective_comparison",
    "plot_jurisdiction_comparison",
    "plot_comprehensive_dashboard",
    "plot_strategy_comparison_grid",
]


def plot_perspective_comparison(
    data_dict: Dict[str, pd.DataFrame],
    output_path: Path,
    metric: str = 'ICER',
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create multi-panel comparison across perspectives.
    
    Args:
        data_dict: Dictionary mapping perspective names to DataFrames
        output_path: Output file path
        metric: Metric to compare
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = f"{metric} Comparison Across Perspectives"
    
    if standards is None:
        standards = JournalStandards()
    
    n_perspectives = len(data_dict)
    
    with journal_style(standards):
        fig = plt.figure(figsize=(12, 4 * n_perspectives), dpi=standards.min_dpi)
        gs = gridspec.GridSpec(n_perspectives, 1, hspace=0.3)
        
        for i, (perspective, data) in enumerate(data_dict.items()):
            ax = fig.add_subplot(gs[i])
            
            # Create bar plot
            strategies = data['strategy'].values
            values = data[metric.lower()].values
            
            _bars = ax.bar(range(len(strategies)), values, alpha=0.7)
            
            # Color bars by cost-effectiveness
            if metric == 'ICER':
                wtp = 50000
                for bar, val in zip(_bars, values):
                    if val < wtp:
                        bar.set_color('green')
                    elif val < wtp * 1.5:
                        bar.set_color('orange')
                    else:
                        bar.set_color('red')
            
            # Set labels
            ax.set_title(f"{perspective} Perspective", fontweight='bold')
            ax.set_ylabel(metric)
            ax.set_xticks(range(len(strategies)))
            ax.set_xticklabels(strategies, rotation=45, ha='right')
            
            # Format y-axis
            if metric == 'ICER' or 'Cost' in metric:
                format_axis_currency(ax, 'y', currency)
            
            # Add value labels
            for j, (bar, val) in enumerate(zip(_bars, values)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val:,.0f}',
                       ha='center', va='bottom', fontsize=7)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_jurisdiction_comparison(
    au_data: pd.DataFrame,
    nz_data: pd.DataFrame,
    output_path: Path,
    metric: str = 'ICER',
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create side-by-side comparison of Australia vs New Zealand.
    
    Args:
        au_data: Australia data
        nz_data: New Zealand data
        output_path: Output file path
        metric: Metric to compare
        title: Optional custom title
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = f"{metric} Comparison: Australia vs New Zealand"
    
    if standards is None:
        standards = JournalStandards()
    
    with journal_style(standards):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=standards.min_dpi)
        
        # Australia plot
        strategies_au = au_data['strategy'].values
        values_au = au_data[metric.lower()].values
        
        ax1.bar(range(len(strategies_au)), values_au, alpha=0.7, color='steelblue')
        ax1.set_title("Australia", fontweight='bold')
        ax1.set_ylabel(metric)
        ax1.set_xticks(range(len(strategies_au)))
        ax1.set_xticklabels(strategies_au, rotation=45, ha='right')
        
        # New Zealand plot
        strategies_nz = nz_data['strategy'].values
        values_nz = nz_data[metric.lower()].values
        
        ax2.bar(range(len(strategies_nz)), values_nz, alpha=0.7, color='darkgreen')
        ax2.set_title("New Zealand", fontweight='bold')
        ax2.set_ylabel(metric)
        ax2.set_xticks(range(len(strategies_nz)))
        ax2.set_xticklabels(strategies_nz, rotation=45, ha='right')
        
        # Format axes
        if metric == 'ICER' or 'Cost' in metric:
            format_axis_currency(ax1, 'y', 'A$')
            format_axis_currency(ax2, 'y', 'NZ$')
        
        # Sync y-axis limits
        y_max = max(ax1.get_ylim()[1], ax2.get_ylim()[1])
        ax1.set_ylim(0, y_max)
        ax2.set_ylim(0, y_max)
        
        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_comprehensive_dashboard(
    cea_data: pd.DataFrame,
    ceac_data: pd.DataFrame,
    evpi_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create comprehensive 4-panel dashboard.
    
    Args:
        cea_data: CEA results
        ceac_data: CEAC data
        evpi_data: EVPI data
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Cost-Effectiveness Analysis Dashboard"
    
    if standards is None:
        standards = JournalStandards()
    
    with journal_style(standards):
        fig = plt.figure(figsize=(14, 10), dpi=standards.min_dpi)
        gs = gridspec.GridSpec(2, 2, hspace=0.3, wspace=0.3)
        
        # Panel 1: ICER bar chart
        ax1 = fig.add_subplot(gs[0, 0])
        strategies = cea_data['strategy'].values
        icers = cea_data['icer'].values
        
        _bars = ax1.bar(range(len(strategies)), icers, alpha=0.7)
        ax1.set_title("Incremental Cost-Effectiveness Ratios", fontweight='bold')
        ax1.set_ylabel(f"ICER ({currency}/QALY)")
        ax1.set_xticks(range(len(strategies)))
        ax1.set_xticklabels(strategies, rotation=45, ha='right')
        format_axis_currency(ax1, 'y', currency)
        
        # Add WTP threshold line
        wtp = 50000
        ax1.axhline(y=wtp, color='red', linestyle='--', linewidth=1.5, 
                   label=f'WTP = {currency}{wtp:,.0f}/QALY')
        ax1.legend(fontsize=8)
        
        # Panel 2: CEAC
        ax2 = fig.add_subplot(gs[0, 1])
        for strategy in ceac_data.columns:
            if strategy == 'wtp':
                continue
            ax2.plot(ceac_data['wtp'], ceac_data[strategy], 
                    label=strategy, linewidth=2)
        
        ax2.set_title("Cost-Effectiveness Acceptability Curves", fontweight='bold')
        ax2.set_xlabel(f"WTP Threshold ({currency}/QALY)")
        ax2.set_ylabel("Probability Cost-Effective")
        # Use WTP formatter so ticks show currency symbol + thousands sep (e.g., A$20,000)
        format_axis_wtp(ax2, currency=currency, thousands=True)
        format_axis_percentage(ax2, 'y', decimals=0)
        ax2.set_ylim(0, 100)
        ax2.legend(fontsize=7, loc='best')
        
        # Panel 3: Cost vs Effect scatter
        ax3 = fig.add_subplot(gs[1, 0])
        for strategy in strategies:
            strategy_data = cea_data[cea_data['strategy'] == strategy]
            ax3.scatter(
                strategy_data['effect'],
                strategy_data['cost'],
                s=100,
                alpha=0.7,
                label=strategy
            )
        
        ax3.set_title("Cost vs Effectiveness", fontweight='bold')
        ax3.set_xlabel("QALYs")
        ax3.set_ylabel(f"Cost ({currency})")
        format_axis_currency(ax3, 'y', currency)
        ax3.legend(fontsize=7, loc='best')
        ax3.grid(True, alpha=0.3)
        
        # Panel 4: EVPI curve
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.plot(evpi_data['wtp'], evpi_data['evpi'], 
                linewidth=2, color='steelblue')
        ax4.fill_between(evpi_data['wtp'], 0, evpi_data['evpi'], 
                         alpha=0.3, color='steelblue')

        ax4.set_title("Expected Value of Perfect Information", fontweight='bold')
        ax4.set_xlabel(f"WTP Threshold ({currency}/QALY)")
        ax4.set_ylabel(f"EVPI per Patient ({currency})")
        # EVPI x-axis is a WTP axis; use the WTP formatter
        format_axis_wtp(ax4, currency=currency, thousands=True)
        format_axis_currency(ax4, 'y', currency, thousands=True)

        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.995)
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_strategy_comparison_grid(
    data_dict: Dict[str, Any],
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create grid comparison of multiple metrics across strategies.
    
    Args:
        data_dict: Dictionary with metric names and DataFrames
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Strategy Comparison Grid"
    
    if standards is None:
        standards = JournalStandards()
    
    n_metrics = len(data_dict)
    n_cols = 2
    n_rows = (n_metrics + 1) // 2
    
    with journal_style(standards):
        fig, axes = plt.subplots(
            n_rows, n_cols,
            figsize=(14, 5 * n_rows),
            dpi=standards.min_dpi
        )
        
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        
        for idx, (metric_name, data) in enumerate(data_dict.items()):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col]
            
            # Create bar plot
            strategies = data['strategy'].values
            values = data['value'].values
            
            ax.bar(range(len(strategies)), values, alpha=0.7)
            ax.set_title(metric_name, fontweight='bold')
            ax.set_xticks(range(len(strategies)))
            ax.set_xticklabels(strategies, rotation=45, ha='right')
            ax.grid(True, alpha=0.3, axis='y')
        
        # Hide unused subplots
        for idx in range(n_metrics, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            axes[row, col].axis('off')
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path
