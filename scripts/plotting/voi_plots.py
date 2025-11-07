"""
Value of Information Analysis Plotting

Publication-quality plots for VOI results.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.plotting.publication import (
    figure_context, save_multiformat, format_axis_currency,
    JournalStandards
)

__all__ = [
    "plot_evpi_curve",
    "plot_evppi_bars",
    "plot_evsi_curve",
    "plot_voi_tornado",
    "plot_evsi_efficiency_curve",
    "plot_research_priorities",
    "plot_trial_design_optimization",
    "plot_evsi_portfolio_analysis",
]


def plot_evpi_curve(
    evpi_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create EVPI curve across WTP thresholds.
    
    Args:
        evpi_data: DataFrame with WTP and EVPI values
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    # Note: WTP (x-axis) tick labels are formatted with the currency symbol
    # and thousands separator for publication clarity (e.g., A$20,000).
    if title is None:
        title = "Expected Value of Perfect Information:\nKetamine vs Electroconvulsive Therapy for Treatment-Resistant Depression"
    
    with figure_context(
        title=title,
        xlabel=f"Willingness-to-Pay Threshold ({currency}/QALY)",
        ylabel=f"Expected Value of Perfect Information\nper Patient ({currency})",
        standards=standards
    ) as (fig, ax):
        
        # Plot EVPI curve
        ax.plot(
            evpi_data['wtp'],
            evpi_data['evpi'],
            linewidth=2,
            color='steelblue'
        )

        # Fill area under curve (baseline at zero)
        ax.fill_between(
            evpi_data['wtp'],
            0,
            evpi_data['evpi'].clip(lower=0),
            alpha=0.3,
            color='steelblue'
        )

        # Format x-axis WTP with currency and thousands separator
        from analysis.plotting.publication import format_axis_wtp, format_axis_currency
        format_axis_wtp(ax, currency=currency, thousands=True)

        # Keep y-axis as currency-formatted
        format_axis_currency(ax, 'y', currency, thousands=True)

        # Tighten x-limits to data with a small margin
        x_min, x_max = float(evpi_data['wtp'].min()), float(evpi_data['wtp'].max())
        x_margin = max(1.0, 0.02 * (x_max - x_min))
        ax.set_xlim(x_min - x_margin, x_max + x_margin)
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_evppi_bars(
    evppi_data: pd.DataFrame,
    output_path: Path,
    wtp: float = 50000,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create EVPPI bar chart for parameters.
    
    Args:
        evppi_data: DataFrame with parameters and EVPPI values
        output_path: Output file path
        wtp: Willingness-to-pay threshold
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = f"Expected Value of Partial Perfect Information:\nParameter Uncertainty in Ketamine vs ECT Analysis\n(WTP = {currency}{wtp:,.0f}/QALY)"
    
    # Sort by EVPPI value
    evppi_data = evppi_data.sort_values('evppi', ascending=True)
    
    with figure_context(
        title=title,
        xlabel=f"Expected Value of Partial Perfect Information\nper Patient ({currency})",
        ylabel="Parameter",
        figsize=(8, max(6, len(evppi_data) * 0.3)),
        standards=standards
    ) as (fig, ax):
        
        # Create horizontal bar chart
        y_pos = np.arange(len(evppi_data))
        ax.barh(
            y_pos,
            evppi_data['evppi'].values,
            alpha=0.7,
            color='steelblue'
        )
        
        # Set y-axis labels
        ax.set_yticks(y_pos)
        ax.set_yticklabels(evppi_data['parameter'].values, fontsize=8)
        
        # Format x-axis
        from analysis.plotting.publication import format_axis_wtp
        format_axis_wtp(ax, currency=currency, thousands=True)
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_evsi_curve(
    evsi_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create EVSI curve across sample sizes.
    
    Args:
        evsi_data: DataFrame with sample sizes and EVSI values
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Expected Value of Sample Information"
    
    with figure_context(
        title=title,
        xlabel="Sample Size",
        ylabel=f"EVSI per Patient ({currency})",
        standards=standards
    ) as (fig, ax):
        
        # Plot EVSI curve
        ax.plot(
            evsi_data['sample_size'],
            evsi_data['evsi'],
            linewidth=2,
            color='steelblue',
            marker='o',
            markersize=4
        )
        
        # Format y-axis
        format_axis_currency(ax, 'y', currency, thousands=True)
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_voi_tornado(
    voi_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create VOI tornado diagram showing research priorities.
    
    Args:
        voi_data: DataFrame with parameters and VOI values
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Value of Information Analysis:\nResearch Priorities for Ketamine vs ECT\nTreatment-Resistant Depression"
    
    # Sort by VOI value
    voi_data = voi_data.sort_values('population_evppi', ascending=True)
    
    with figure_context(
        title=title,
        xlabel=f"Population Expected Value of Partial Perfect Information\n({currency} millions)",
        ylabel="Parameter",
        figsize=(8, max(6, len(voi_data) * 0.3)),
        standards=standards
    ) as (fig, ax):
        
        # Create horizontal bar chart
        y_pos = np.arange(len(voi_data))
        values = voi_data['population_evppi'].values / 1e6  # Convert to millions
        
        # Color bars by priority
        colors = ['red' if v > 10 else 'orange' if v > 5 else 'steelblue' 
                 for v in values]
        
        ax.barh(
            y_pos,
            values,
            alpha=0.7,
            color=colors
        )
        
        # Set y-axis labels
        ax.set_yticks(y_pos)
        ax.set_yticklabels(voi_data['parameter'].values, fontsize=8)
        
        # Add value labels
        for i, v in enumerate(values):
            ax.text(v, i, f' {v:.1f}M', va='center', fontsize=7)
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_evsi_efficiency_curve(
    evsi_data: pd.DataFrame,
    research_cost_per_patient: float,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create EVSI efficiency curve showing net benefit vs sample size.
    
    Args:
        evsi_data: DataFrame with EVSI values and sample sizes
        research_cost_per_patient: Cost per patient for research
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "EVSI Efficiency Analysis"
    
    # Calculate net benefits
    research_costs = evsi_data['sample_size'] * research_cost_per_patient
    net_benefits = evsi_data['evsi_mean'] - research_costs
    
    with figure_context(
        title=title,
        xlabel="Sample Size",
        ylabel=f"Expected Net Benefit ({currency})",
        standards=standards
    ) as (fig, ax):
        
        # Plot EVSI and research costs
        ax.plot(evsi_data['sample_size'], evsi_data['evsi_mean'],
               label='EVSI', color='steelblue', linewidth=2, marker='o')
        ax.plot(evsi_data['sample_size'], research_costs,
               label='Research Cost', color='firebrick', linewidth=2, linestyle='--')
        ax.plot(evsi_data['sample_size'], net_benefits,
               label='Net Benefit', color='forestgreen', linewidth=3, marker='s')
        
        # Add zero line
        ax.axhline(y=0, color='black', linestyle=':', alpha=0.5)
        
        # Find optimal point
        optimal_idx = net_benefits.argmax()
        optimal_n = evsi_data.iloc[optimal_idx]['sample_size']
        optimal_nb = net_benefits.iloc[optimal_idx]
        
        ax.scatter([optimal_n], [optimal_nb], color='red', s=100, zorder=5,
                  label=f'Optimal (n={int(optimal_n)})')
        
        ax.legend()
        format_axis_currency(ax, 'y', currency, thousands=True)
        
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_research_priorities(
    priorities_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create research priorities visualization.
    
    Args:
        priorities_data: DataFrame with parameter research priorities
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Research Priorities Analysis"
    
    with figure_context(
        title=title,
        xlabel="Research Priority Score",
        ylabel="Parameters",
        standards=standards
    ) as (fig, ax):
        
        # Create horizontal bar chart
        y_pos = np.arange(len(priorities_data))
        bars = ax.barh(y_pos, priorities_data['research_priority_score'],
                      color='skyblue', alpha=0.8)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(priorities_data['parameter'])
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + max(priorities_data['research_priority_score']) * 0.01,
                   bar.get_y() + bar.get_height()/2,
                   f'{width:,.0f}',
                   ha='left', va='center', fontweight='bold')
        
        # Format x-axis
        format_axis_currency(ax, 'x', currency, thousands=True)
        
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_trial_design_optimization(
    trial_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create trial design optimization visualization.
    
    Args:
        trial_data: DataFrame with trial design data
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Trial Design Optimization"
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    # EVSI vs Sample Size
    ax1.plot(trial_data['sample_size'], trial_data['evsi'],
            color='steelblue', linewidth=2, marker='o')
    ax1.set_title('EVSI vs Sample Size')
    ax1.set_xlabel('Sample Size')
    ax1.set_ylabel(f'EVSI ({currency})')
    format_axis_currency(ax1, 'y', currency)
    
    # Expected Net Benefit
    ax2.plot(trial_data['sample_size'], trial_data['expected_net_benefit'],
            color='forestgreen', linewidth=2, marker='s')
    ax2.axhline(y=0, color='black', linestyle=':', alpha=0.5)
    ax2.set_title('Expected Net Benefit')
    ax2.set_xlabel('Sample Size')
    ax2.set_ylabel(f'Net Benefit ({currency})')
    format_axis_currency(ax2, 'y', currency)
    
    # Efficiency Ratio
    ax3.plot(trial_data['sample_size'], trial_data['efficiency_ratio'],
            color='orange', linewidth=2, marker='^')
    ax3.set_title('Efficiency Ratio')
    ax3.set_xlabel('Sample Size')
    ax3.set_ylabel('EVSI per Research Dollar')
    
    # Statistical Power
    if 'statistical_power' in trial_data.columns:
        ax4.plot(trial_data['sample_size'], trial_data['statistical_power'],
                color='purple', linewidth=2, marker='d')
        ax4.axhline(y=0.8, color='red', linestyle='--', alpha=0.7, label='80% Power')
        ax4.set_title('Statistical Power')
        ax4.set_xlabel('Sample Size')
        ax4.set_ylabel('Power')
        ax4.legend()
    
    plt.tight_layout()
    
    # Save figure
    artifacts = save_multiformat(fig, output_path, standards=standards)
    plt.close(fig)
    
    return artifacts.base_path


def plot_evsi_portfolio_analysis(
    portfolio_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create research portfolio optimization visualization.
    
    Args:
        portfolio_data: DataFrame with portfolio analysis data
        output_path: Output file path
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Research Portfolio Optimization"
    
    with figure_context(
        title=title,
        xlabel="Research Investment",
        ylabel=f"Expected Value ({currency})",
        standards=standards
    ) as (fig, ax):
        
        # Plot efficient frontier (mock data for illustration)
        investment_levels = np.linspace(0, 1000000, 50)
        evsi_values = 50000 * (1 - np.exp(-investment_levels / 200000))
        uncertainty = 5000 * np.random.randn(len(investment_levels)) * 0.1
        
        ax.fill_between(investment_levels, evsi_values - uncertainty,
                       evsi_values + uncertainty, alpha=0.3, color='lightblue')
        ax.plot(investment_levels, evsi_values, color='steelblue',
               linewidth=2, label='Expected EVSI')
        
        # Add reference lines
        ax.axhline(y=0, color='black', linestyle=':', alpha=0.5)
        ax.axvline(x=250000, color='red', linestyle='--', alpha=0.7,
                  label='Optimal Investment')
        
        ax.legend()
        format_axis_currency(ax, 'x', currency, thousands=True)
        format_axis_currency(ax, 'y', currency, thousands=True)
        
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path
