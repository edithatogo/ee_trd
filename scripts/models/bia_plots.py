"""
Budget Impact Analysis Visualization

Publication-quality plots for budget impact analysis.
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


def plot_annual_budget_impact(
    bia_data: pd.DataFrame,
    output_path: Path,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot annual budget impact over time.
    
    Args:
        bia_data: DataFrame with columns ['year', 'budget_impact', 'perspective']
        output_path: Output file path
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Annual Budget Impact: Ketamine vs Electroconvulsive Therapy for Treatment-Resistant Depression'
    
    # Handle different column names
    _impact_col = 'annual_impact' if 'annual_impact' in bia_data.columns else 'budget_impact'
    
    with figure_context(
        title=title,
        xlabel='Year',
        ylabel=f'Annual Budget Impact ({currency})'
    ) as (fig, ax):
        
        # Plot budget impact - handle if no perspective column
        if 'perspective' in bia_data.columns:
            for perspective in bia_data['perspective'].unique():
                perspective_data = bia_data[bia_data['perspective'] == perspective]
                ax.plot(
                    perspective_data['year'],
                    perspective_data[_impact_col],
                    label=perspective,
                    linewidth=2,
                    marker='o',
                    markersize=6
                )
        else:
            ax.plot(
                bia_data['year'],
                bia_data[_impact_col],
                linewidth=2,
                marker='o',
                markersize=6
            )
        
        # Add zero reference line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        
        # Formatting
        format_axis_currency(ax, axis='y', currency=currency)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        if 'perspective' in bia_data.columns:
            create_legend(ax, loc='best')
        
        return save_multiformat(fig, output_path)


def plot_cumulative_budget_impact(
    bia_data: pd.DataFrame,
    output_path: Path,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot cumulative budget impact over time.
    
    Args:
        bia_data: DataFrame with columns ['year', 'cumulative_impact', 'perspective']
        output_path: Output file path
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Cumulative Budget Impact: Ketamine vs Electroconvulsive Therapy for Treatment-Resistant Depression'
    
    with figure_context(
        title=title,
        xlabel='Year',
        ylabel=f'Cumulative Budget Impact ({currency})'
    ) as (fig, ax):
        
        # Plot cumulative impact - handle if no perspective column
        if 'perspective' in bia_data.columns:
            for perspective in bia_data['perspective'].unique():
                perspective_data = bia_data[bia_data['perspective'] == perspective]
                ax.plot(
                    perspective_data['year'],
                    perspective_data['cumulative_impact'],
                    label=perspective,
                    linewidth=2,
                    marker='s',
                    markersize=6
                )
                
                # Fill area under curve
                ax.fill_between(
                    perspective_data['year'],
                    0,
                    perspective_data['cumulative_impact'],
                    alpha=0.2
                )
        else:
            ax.plot(
                bia_data['year'],
                bia_data['cumulative_impact'],
                linewidth=2,
                marker='s',
                markersize=6
            )
            ax.fill_between(
                bia_data['year'],
                0,
                bia_data['cumulative_impact'],
                alpha=0.2
            )
        
        # Add zero reference line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        
        # Formatting
        format_axis_currency(ax, axis='y', currency=currency)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        if 'perspective' in bia_data.columns:
            create_legend(ax, loc='best')
        
        return save_multiformat(fig, output_path)


def plot_market_share_evolution(
    market_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot market share evolution over time.
    
    Args:
        market_data: DataFrame with columns ['year', 'market_share', 'strategy']
        output_path: Output file path
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Market Share Evolution: Adoption of Ketamine Therapies vs Electroconvulsive Therapy'
    
    with figure_context(
        title=title,
        xlabel='Year',
        ylabel='Market Share (%)'
    ) as (fig, ax):
        
        # Create stacked area plot
        strategies = market_data['strategy'].unique()
        years = market_data['year'].unique()
        
        # Pivot data for stacking
        pivot_data = market_data.pivot(index='year', columns='strategy', values='market_share')
        
        ax.stackplot(
            years,
            *[pivot_data[strategy].values for strategy in strategies],
            labels=strategies,
            alpha=0.8
        )
        
        # Formatting
        format_axis_percentage(ax, axis='y')
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        create_legend(ax, loc='best')
        
        return save_multiformat(fig, output_path)


def plot_budget_impact_breakdown(
    breakdown_data: pd.DataFrame,
    output_path: Path,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot budget impact breakdown by cost category.
    
    Args:
        breakdown_data: DataFrame with columns ['category', 'cost', 'strategy']
        output_path: Output file path
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Budget Impact Breakdown: Cost Categories for Ketamine vs ECT Treatment'
    
    # Handle different column names
    if 'drug_cost' in breakdown_data.columns:
        categories = ['drug_cost', 'admin_cost', 'monitoring_cost']
    else:
        categories = breakdown_data['category'].unique() if 'category' in breakdown_data.columns else []
    
    with figure_context(
        title=title,
        xlabel='Strategy',
        ylabel=f'Total Cost ({currency})',
        figsize=(12, 6)
    ) as (fig, ax):
        
        # Plot stacked bar chart
        strategies = breakdown_data['strategy'].unique()
        categories = breakdown_data['category'].unique()
        x = np.arange(len(strategies))
        
        bottom = np.zeros(len(strategies))
        for category in categories:
            category_costs = [
                breakdown_data[(breakdown_data['strategy'] == s) & 
                              (breakdown_data['category'] == category)]['cost'].values[0]
                if len(breakdown_data[(breakdown_data['strategy'] == s) & 
                                     (breakdown_data['category'] == category)]) > 0
                else 0
                for s in strategies
            ]
            ax.bar(x, category_costs, label=category, bottom=bottom, alpha=0.8)
            bottom += category_costs
        
        # Formatting
        ax.set_xticks(x)
        ax.set_xticklabels(strategies, rotation=45, ha='right')
        format_axis_currency(ax, axis='y', currency=currency)
        
        ax.set_xlabel('Strategy', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'Total Cost ({currency})', fontsize=12, fontweight='bold')
        
        if title is None:
            title = 'Budget Impact Breakdown: Cost Categories for Ketamine vs ECT Treatment'
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        create_legend(ax, loc='best')
        
        return save_multiformat(fig, output_path)


def plot_population_impact(
    population_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot population impact over time.
    
    Args:
        population_data: DataFrame with columns ['year', 'n_patients', 'strategy']
        output_path: Output file path
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Population Impact: Treatment-Resistant Depression Patients Receiving Ketamine vs ECT'
    
    # Handle different column names
    _patient_col = 'patients' if 'patients' in population_data.columns else 'n_patients'
    
    with figure_context(
        title=title,
        xlabel='Year',
        ylabel='Number of Patients'
    ) as (fig, ax):
        
        # Plot patient numbers by strategy
        for strategy in population_data['strategy'].unique():
            strategy_data = population_data[population_data['strategy'] == strategy]
            ax.plot(
                strategy_data['year'],
                strategy_data['n_patients'],
                label=strategy,
                linewidth=2,
                marker='o',
                markersize=6
            )
        
        # Formatting
        
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Format y-axis with thousands separator
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        
        create_legend(ax, loc='best')
        
        return save_multiformat(fig, output_path)


def plot_affordability_analysis(
    affordability_data: pd.DataFrame,
    output_path: Path,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot affordability analysis showing budget impact vs budget capacity.
    
    Args:
        affordability_data: DataFrame with columns ['year', 'budget_impact', 'budget_capacity', 'perspective']
        output_path: Output file path
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Affordability Analysis: Budget Impact vs Healthcare Capacity for Ketamine vs ECT'
    
    with figure_context(
        title=title,
        xlabel='Year',
        ylabel=f'Budget ({currency})'
    ) as (fig, ax):
        
        # Plot budget impact and capacity
        for perspective in affordability_data['perspective'].unique():
            perspective_data = affordability_data[affordability_data['perspective'] == perspective]
            
            ax.plot(
                perspective_data['year'],
                perspective_data['budget_impact'],
                label=f'{perspective} - Impact',
                linewidth=2,
                marker='o',
                markersize=6
            )
            
            ax.plot(
                perspective_data['year'],
                perspective_data['budget_capacity'],
                label=f'{perspective} - Capacity',
                linewidth=2,
                linestyle='--',
                marker='s',
                markersize=6
            )
        
        # Add zero reference line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        
        # Formatting
        format_axis_currency(ax, axis='y', currency=currency)
        
        ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'Budget ({currency})', fontsize=12, fontweight='bold')
        
        if title is None:
            title = 'Affordability Analysis: Budget Impact vs Healthcare Capacity for Ketamine vs ECT'
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.3, linestyle='--')
        
        create_legend(ax, loc='best', ncol=2)
        
        return save_multiformat(fig, output_path)


def plot_scenario_comparison(
    scenario_data: pd.DataFrame,
    output_path: Path,
    currency: str = "A$",
    title: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Plot budget impact across different scenarios.
    
    Args:
        scenario_data: DataFrame with columns ['scenario', 'total_impact', 'perspective']
        output_path: Output file path
        currency: Currency symbol
        title: Optional custom title
        **kwargs: Additional plotting parameters
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = 'Budget Impact Scenario Comparison: Ketamine vs Electroconvulsive Therapy Adoption'
    
    # Handle different column names
    _impact_col = 'annual_cost' if 'annual_cost' in scenario_data.columns else 'total_impact'
    group_col = 'strategy' if 'strategy' in scenario_data.columns else 'perspective'
    
    with figure_context(
        title=title,
        xlabel='Scenario',
        ylabel=f'Total Budget Impact ({currency})'
    ) as (fig, ax):
        
        # Plot budget impact by scenario
        # Group by strategy if multiple strategies, otherwise by perspective
        if 'strategy' in scenario_data.columns and len(scenario_data['strategy'].unique()) > 1:
            groups = scenario_data['strategy'].unique()
            group_col = 'strategy'
        else:
            groups = scenario_data['perspective'].unique() if 'perspective' in scenario_data.columns else ['All']
            group_col = 'perspective' if 'perspective' in scenario_data.columns else None
        
        scenarios = scenario_data['scenario'].unique()
        x = np.arange(len(scenarios))
        width = 0.8 / len(groups)
        
        for i, group in enumerate(groups):
            if group_col:
                group_data = scenario_data[scenario_data[group_col] == group]
            else:
                group_data = scenario_data
            
            # Aggregate by scenario if multiple rows per scenario
            scenario_totals = group_data.groupby('scenario')['total_impact'].sum().reindex(scenarios)
            
            offset = (i - len(groups)/2 + 0.5) * width
            ax.bar(
                x + offset,
                scenario_totals.values,
                width,
                label=group,
                alpha=0.8
            )
        
        # Add zero reference line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        
        # Formatting
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        format_axis_currency(ax, axis='y', currency=currency)
        
        ax.set_xlabel('Scenario', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'Total Budget Impact ({currency})', fontsize=12, fontweight='bold')
        
        if title is None:
            title = 'Budget Impact Scenario Comparison: Ketamine vs Electroconvulsive Therapy Adoption'
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        create_legend(ax, loc='best')
        
        return save_multiformat(fig, output_path)
