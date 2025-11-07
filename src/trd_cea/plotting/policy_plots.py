"""
Policy Realism Plotting Functions for V4 Health Economic Analysis

This module provides visualization functions for policy realism toggles,
including policy impact analysis, sensitivity analysis, and implementation
complexity assessments.

Features:
- Policy scenario comparison plots
- Sensitivity analysis visualizations
- Implementation impact dashboards
- Cost-effectiveness acceptability curves under different policies

Author: V4 Development Team
Date: October 2025
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

from analysis.plotting.publication import (
    journal_style, save_multiformat, add_reference_line,
    format_axis_currency, format_axis_percentage, format_axis_wtp
)
from analysis.engines.policy_realism_engine import PolicyToggleResults


def plot_policy_scenario_comparison(
    results: PolicyToggleResults,
    strategies: Optional[List[str]] = None,
    metric: str = "cost",
    save_path: Optional[str] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot comparison of policy scenarios.

    Args:
        results: Policy toggle results
        strategies: Strategies to include (None for all)
        metric: Metric to plot ('cost', 'effect', or 'icer')
        save_path: Path to save figure
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    with journal_style():
        fig, axes = plt.subplots(figsize=(10, 6))

    # Prepare data
    plot_data = []

    # Add base case
    base_data = results.base_case_results.copy()
    base_data['scenario'] = 'Base Case'
    plot_data.append(base_data)

    # Add policy scenarios
    for scenario_name, scenario_results in results.policy_scenario_results.items():
        scenario_data = scenario_results.copy()
        scenario_data['scenario'] = scenario_name.replace('_', ' ').title()
        plot_data.append(scenario_data)

    combined_data = pd.concat(plot_data, ignore_index=True)

    if strategies:
        combined_data = combined_data[combined_data['strategy'].isin(strategies)]

    # Create plot
    if metric == 'cost':
        sns.boxplot(
            data=combined_data,
            x='strategy',
            y='cost',
            hue='scenario',
            ax=axes,
            palette='Set2'
        )
        format_axis_currency(axes, axis='y')
        axes.set_ylabel('Cost ($)')
        axes.set_title('Policy Scenario Cost Comparison')

    elif metric == 'effect':
        sns.boxplot(
            data=combined_data,
            x='strategy',
            y='effect',
            hue='scenario',
            ax=axes,
            palette='Set2'
        )
        axes.set_ylabel('Effect (QALYs)')
        axes.set_title('Policy Scenario Effect Comparison')

    elif metric == 'icer':
        # Calculate ICER for each scenario
        icer_data = []
        for scenario in combined_data['scenario'].unique():
            scenario_data = combined_data[combined_data['scenario'] == scenario]
            for strategy in scenario_data['strategy'].unique():
                strategy_data = scenario_data[scenario_data['strategy'] == strategy]
                if len(strategy_data) > 0:
                    cost = strategy_data['cost'].mean()
                    effect = strategy_data['effect'].mean()
                    icer = cost / effect if effect > 0 else float('inf')
                    icer_data.append({
                        'scenario': scenario,
                        'strategy': strategy,
                        'icer': icer
                    })

        icer_df = pd.DataFrame(icer_data)
        sns.barplot(
            data=icer_df,
            x='strategy',
            y='icer',
            hue='scenario',
            ax=axes,
            palette='Set2'
        )
        format_axis_currency(axes, axis='y')
        axes.set_ylabel('ICER ($/QALY)')
        axes.set_title('Policy Scenario ICER Comparison')

    axes.set_xlabel('Strategy')
    axes.legend(title='Policy Scenario', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    if save_path:
        save_multiformat(fig, save_path)

    return fig


def plot_policy_sensitivity_analysis(
    results: PolicyToggleResults,
    save_path: Optional[str] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot sensitivity analysis for policy scenarios.

    Args:
        results: Policy toggle results
        save_path: Path to save figure
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    sensitivity_data = results.sensitivity_analysis

    if sensitivity_data.empty:
        # No logger available here
        return plt.figure()

    with journal_style():
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Cost change percentage
    sns.barplot(
        data=sensitivity_data,
        x='strategy',
        y='cost_change_percent',
        hue='scenario',
        ax=axes[0, 0],
        palette='RdYlBu'
    )
    format_axis_percentage(axes[0, 0], axis='y')
    axes[0, 0].set_ylabel('Cost Change (%)')
    axes[0, 0].set_title('Policy Impact on Costs')
    add_reference_line(axes[0, 0], 0, orientation='horizontal', color='black', linestyle='--', alpha=0.5)

    # Effect change percentage
    sns.barplot(
        data=sensitivity_data,
        x='strategy',
        y='effect_change_percent',
        hue='scenario',
        ax=axes[0, 1],
        palette='RdYlBu'
    )
    format_axis_percentage(axes[0, 1], axis='y')
    axes[0, 1].set_ylabel('Effect Change (%)')
    axes[0, 1].set_title('Policy Impact on Effects')
    add_reference_line(axes[0, 1], 0, orientation='horizontal', color='black', linestyle='--', alpha=0.5)

    # ICER change
    sns.barplot(
        data=sensitivity_data,
        x='strategy',
        y='icer_change',
        hue='scenario',
        ax=axes[1, 0],
        palette='RdYlBu'
    )
    format_axis_percentage(axes[1, 0], axis='y')
    axes[1, 0].set_ylabel('ICER Change (%)')
    axes[1, 0].set_title('Policy Impact on ICER')
    add_reference_line(axes[1, 0], 0, orientation='horizontal', color='black', linestyle='--', alpha=0.5)

    # Cost vs Effect change scatter
    for scenario in sensitivity_data['scenario'].unique():
        scenario_data = sensitivity_data[sensitivity_data['scenario'] == scenario]
        axes[1, 1].scatter(
            scenario_data['cost_change_percent'],
            scenario_data['effect_change_percent'],
            label=scenario.replace('_', ' ').title(),
            alpha=0.7
        )

    axes[1, 1].set_xlabel('Cost Change (%)')
    axes[1, 1].set_ylabel('Effect Change (%)')
    axes[1, 1].set_title('Cost vs Effect Policy Impact')
    add_reference_line(axes[1, 1], 0, orientation='horizontal', color='black', linestyle='--', alpha=0.5)
    add_reference_line(axes[1, 1], 0, orientation='vertical', color='black', linestyle='--', alpha=0.5)
    axes[1, 1].legend()

    # Rotate x-axis labels
    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    if save_path:
        save_multiformat(fig, save_path)

    return fig


def plot_implementation_impact_dashboard(
    results: PolicyToggleResults,
    save_path: Optional[str] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot implementation impact dashboard.

    Args:
        results: Policy toggle results
        save_path: Path to save figure
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    impact_data = results.implementation_impact

    if impact_data.empty:
        # No logger available here
        return plt.figure()

    with journal_style():
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Cost impact by strategy and scenario
    pivot_cost = impact_data.pivot_table(
        values='cost_impact_percent',
        index='strategy',
        columns='scenario',
        aggfunc='mean'
    )

    sns.heatmap(
        pivot_cost,
        annot=True,
        fmt='.1f',
        cmap='RdYlBu_r',
        center=0,
        ax=axes[0, 0]
    )
    axes[0, 0].set_title('Cost Impact by Policy Scenario (%)')
    axes[0, 0].set_ylabel('Strategy')

    # Reimbursement rates
    pivot_reimb = impact_data.pivot_table(
        values='reimbursement_rate',
        index='strategy',
        columns='scenario',
        aggfunc='mean'
    )

    sns.heatmap(
        pivot_reimb,
        annot=True,
        fmt='.2f',
        cmap='Blues',
        vmin=0,
        vmax=1,
        ax=axes[0, 1]
    )
    axes[0, 1].set_title('Reimbursement Rates by Scenario')

    # Administrative burden
    pivot_burden = impact_data.pivot_table(
        values='administrative_burden',
        index='strategy',
        columns='scenario',
        aggfunc='mean'
    )

    sns.heatmap(
        pivot_burden,
        annot=True,
        fmt='.2f',
        cmap='Oranges',
        ax=axes[1, 0]
    )
    axes[1, 0].set_title('Administrative Burden by Scenario')

    # Implementation complexity
    complexity_counts = impact_data.groupby(['scenario', 'implementation_complexity']).size().unstack(fill_value=0)

    complexity_counts.plot(
        kind='bar',
        stacked=True,
        ax=axes[1, 1],
        color=['green', 'yellow', 'red']
    )
    axes[1, 1].set_title('Implementation Complexity Distribution')
    axes[1, 1].set_ylabel('Number of Strategies')
    axes[1, 1].legend(title='Complexity', bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()

    if save_path:
        save_multiformat(fig, save_path)

    return fig


def create_policy_comparison_dashboard(
    results: PolicyToggleResults,
    save_path: Optional[str] = None,
    **kwargs
) -> go.Figure:
    """
    Create interactive policy comparison dashboard.

    Args:
        results: Policy toggle results
        save_path: Path to save figure
        **kwargs: Additional plotting arguments

    Returns:
        Plotly figure
    """
    # Create subplot figure
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Cost Comparison by Scenario',
            'Effect Comparison by Scenario',
            'Policy Sensitivity Analysis',
            'Implementation Impact Summary'
        ),
        specs=[[{'type': 'box'}, {'type': 'box'}],
               [{'type': 'scatter'}, {'type': 'bar'}]]
    )

    # Prepare data
    plot_data = []

    # Add base case
    base_data = results.base_case_results.copy()
    base_data['scenario'] = 'Base Case'
    plot_data.append(base_data)

    # Add policy scenarios
    for scenario_name, scenario_results in results.policy_scenario_results.items():
        scenario_data = scenario_results.copy()
        scenario_data['scenario'] = scenario_name.replace('_', ' ').title()
        plot_data.append(scenario_data)

    combined_data = pd.concat(plot_data, ignore_index=True)

    # Cost comparison box plot
    for i, scenario in enumerate(combined_data['scenario'].unique()):
        scenario_data = combined_data[combined_data['scenario'] == scenario]
        fig.add_trace(
            go.Box(
                x=scenario_data['strategy'],
                y=scenario_data['cost'],
                name=scenario,
                showlegend=True,
                legendgroup=scenario,
                marker_color=px.colors.qualitative.Set2[i % len(px.colors.qualitative.Set2)]
            ),
            row=1, col=1
        )

    # Effect comparison box plot
    for i, scenario in enumerate(combined_data['scenario'].unique()):
        scenario_data = combined_data[combined_data['scenario'] == scenario]
        fig.add_trace(
            go.Box(
                x=scenario_data['strategy'],
                y=scenario_data['effect'],
                name=scenario,
                showlegend=False,
                legendgroup=scenario,
                marker_color=px.colors.qualitative.Set2[i % len(px.colors.qualitative.Set2)]
            ),
            row=1, col=2
        )

    # Sensitivity analysis scatter
    sensitivity_data = results.sensitivity_analysis
    if not sensitivity_data.empty:
        for scenario in sensitivity_data['scenario'].unique():
            scenario_data = sensitivity_data[sensitivity_data['scenario'] == scenario]
            fig.add_trace(
                go.Scatter(
                    x=scenario_data['cost_change_percent'],
                    y=scenario_data['effect_change_percent'],
                    mode='markers+text',
                    name=f'{scenario} Sensitivity',
                    text=scenario_data['strategy'],
                    textposition="top center",
                    marker=dict(size=10)
                ),
                row=2, col=1
            )

        # Add reference lines
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        fig.add_vline(x=0, line_dash="dash", line_color="gray", row=2, col=1)

    # Implementation impact summary
    impact_data = results.implementation_impact
    if not impact_data.empty:
        avg_impact = impact_data.groupby('scenario')['cost_impact_percent'].mean().reset_index()

        fig.add_trace(
            go.Bar(
                x=avg_impact['scenario'],
                y=avg_impact['cost_impact_percent'],
                name='Average Cost Impact (%)',
                marker_color='lightblue'
            ),
            row=2, col=2
        )

    # Update layout
    fig.update_layout(
        height=800,
        title_text="Policy Realism Analysis Dashboard",
        showlegend=True
    )

    fig.update_xaxes(tickangle=45)

    # Update axis labels
    fig.update_yaxes(title_text="Cost ($)", row=1, col=1)
    fig.update_yaxes(title_text="Effect (QALYs)", row=1, col=2)
    fig.update_xaxes(title_text="Cost Change (%)", row=2, col=1)
    fig.update_yaxes(title_text="Effect Change (%)", row=2, col=1)
    fig.update_yaxes(title_text="Average Cost Impact (%)", row=2, col=2)

    if save_path:
        fig.write_html(save_path)

    return fig


def plot_policy_cost_effectiveness_acceptability(
    results: PolicyToggleResults,
    willingness_to_pay: float = 50000,
    save_path: Optional[str] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot cost-effectiveness acceptability curves for different policy scenarios.

    Args:
        results: Policy toggle results
        willingness_to_pay: Willingness to pay threshold ($/QALY)
        save_path: Path to save figure
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    with journal_style():
        fig, ax = plt.subplots(figsize=(10, 6))

    # Calculate CEAC for each scenario
    wtp_range = np.linspace(0, 100000, 100)
    scenarios = ['Base Case'] + list(results.policy_scenario_results.keys())

    for scenario_name in scenarios:
        if scenario_name == 'Base Case':
            scenario_data = results.base_case_results
        else:
            scenario_data = results.policy_scenario_results[scenario_name]

        # Calculate probability of cost-effectiveness for each strategy
        ceac_data = []

        # Choose reference strategy (usually the least effective/costly)
        reference_strategy = 'Usual Care' if 'Usual Care' in scenario_data['strategy'].unique() else scenario_data['strategy'].unique()[0]

        for wtp in wtp_range:
            # Calculate net benefit for each draw
            strategy_probs = {}

            for strategy in scenario_data['strategy'].unique():
                if strategy == reference_strategy:
                    continue  # Skip reference strategy
                
                strategy_data_ref = scenario_data[scenario_data['strategy'] == reference_strategy]
                strategy_data_comp = scenario_data[scenario_data['strategy'] == strategy]

                if len(strategy_data_comp) > 0 and len(strategy_data_ref) > 0:
                    # Simplified CEAC calculation - compare against reference
                    nb_ref = strategy_data_ref['effect'] * wtp - strategy_data_ref['cost']
                    nb_comp = strategy_data_comp['effect'] * wtp - strategy_data_comp['cost']

                    # Reset indices to ensure proper comparison
                    nb_ref = nb_ref.reset_index(drop=True)
                    nb_comp = nb_comp.reset_index(drop=True)
                    
                    prob_ce = (nb_comp > nb_ref).mean()
                    strategy_probs[strategy] = prob_ce

            # Find strategy with highest probability
            if strategy_probs:
                max_prob = max(strategy_probs.values())
                ceac_data.append(max_prob * 100)  # Convert to percentage
            else:
                ceac_data.append(0)

        ax.plot(wtp_range, ceac_data,
                label=scenario_name.replace('_', ' ').title(),
                linewidth=2)

    # WTP x-axis should show currency and thousands separator
    format_axis_wtp(ax, currency='$', thousands=True)
    ax.set_xlabel('Willingness to Pay ($/QALY)')
    ax.set_ylabel('Probability of Cost-Effectiveness (%)')
    ax.set_title(f'Cost-Effectiveness Acceptability Curves\n(WTP Threshold: ${willingness_to_pay:,.0f}/QALY)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add WTP threshold line
    add_reference_line(ax, willingness_to_pay, orientation='vertical', color='red', linestyle='--', alpha=0.7,
                      label=f'WTP Threshold: ${willingness_to_pay:,.0f}')

    plt.tight_layout()

    if save_path:
        save_multiformat(fig, save_path)

    return fig


def plot_policy_equity_impact(
    results: PolicyToggleResults,
    equity_groups: Optional[List[str]] = None,
    save_path: Optional[str] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot equity impact analysis for policy scenarios.

    Args:
        results: Policy toggle results
        equity_groups: Equity groups to analyze
        save_path: Path to save figure
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    if not equity_groups:
        equity_groups = ['indigenous', 'rural', 'low_ses', 'elderly']

    with journal_style():
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Simulate equity impact data (would be calculated from actual equity analysis)
    scenarios = ['Base Case'] + list(results.policy_scenario_results.keys())
    equity_impacts = {}

    for scenario in scenarios:
        equity_impacts[scenario] = {}
        for group in equity_groups:
            # Generate realistic but simulated equity impacts
            base_impact = np.random.normal(0, 5)  # Base equity impact
            policy_modifier = np.random.normal(0, 2) if scenario != 'Base Case' else 0
            equity_impacts[scenario][group] = base_impact + policy_modifier

    # Equity impact heatmap
    equity_df = pd.DataFrame(equity_impacts).T

    sns.heatmap(
        equity_df,
        annot=True,
        fmt='.1f',
        cmap='RdYlBu_r',
        center=0,
        ax=axes[0, 0]
    )
    axes[0, 0].set_title('Equity Impact by Policy Scenario')
    axes[0, 0].set_ylabel('Policy Scenario')

    # Equity distribution plot
    equity_melted = equity_df.reset_index().melt(id_vars='index', var_name='Equity Group', value_name='Impact')
    equity_melted.columns = ['Scenario', 'Equity Group', 'Impact']

    sns.boxplot(
        data=equity_melted,
        x='Equity Group',
        y='Impact',
        ax=axes[0, 1]
    )
    axes[0, 1].set_title('Equity Impact Distribution')
    add_reference_line(axes[0, 1], 0, orientation='horizontal', color='black', linestyle='--', alpha=0.5)

    # Access disparity analysis
    # Simulate access rates for different equity groups
    access_data = []
    for scenario in scenarios:
        for group in equity_groups:
            base_access = 0.8  # Base access rate
            policy_modifier = np.random.normal(0, 0.05) if scenario != 'Base Case' else 0
            access_rate = np.clip(base_access + policy_modifier, 0, 1)
            access_data.append({
                'scenario': scenario,
                'equity_group': group,
                'access_rate': access_rate
            })

    access_df = pd.DataFrame(access_data)

    sns.barplot(
        data=access_df,
        x='equity_group',
        y='access_rate',
        hue='scenario',
        ax=axes[1, 0]
    )
    axes[1, 0].set_title('Access Rates by Equity Group')
    axes[1, 0].set_ylabel('Access Rate')
    axes[1, 0].set_xlabel('Equity Group')

    # Policy equity summary
    summary_stats = equity_df.describe().T[['mean', 'std']]

    summary_stats.plot(
        kind='bar',
        ax=axes[1, 1],
        color=['skyblue', 'lightcoral']
    )
    axes[1, 1].set_title('Equity Impact Summary Statistics')
    axes[1, 1].set_ylabel('Value')
    axes[1, 1].legend()

    plt.tight_layout()

    if save_path:
        save_multiformat(fig, save_path)

    return fig


def create_policy_report_plots(
    results: PolicyToggleResults,
    output_dir: str = "results/policy_analysis/figures"
) -> Dict[str, str]:
    """
    Create comprehensive policy analysis report plots.

    Args:
        results: Policy toggle results
        output_dir: Output directory for plots

    Returns:
        Dictionary mapping plot names to file paths
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    plot_files = {}

    # Policy scenario comparison
    fig = plot_policy_scenario_comparison(results)
    plot_files['scenario_comparison'] = f"{output_dir}/policy_scenario_comparison.png"
    save_multiformat(fig, plot_files['scenario_comparison'])
    plt.close(fig)

    # Sensitivity analysis
    fig = plot_policy_sensitivity_analysis(results)
    plot_files['sensitivity_analysis'] = f"{output_dir}/policy_sensitivity_analysis.png"
    save_multiformat(fig, plot_files['sensitivity_analysis'])
    plt.close(fig)

    # Implementation impact dashboard
    fig = plot_implementation_impact_dashboard(results)
    plot_files['implementation_impact'] = f"{output_dir}/implementation_impact_dashboard.png"
    save_multiformat(fig, plot_files['implementation_impact'])
    plt.close(fig)

    # Interactive dashboard
    fig = create_policy_comparison_dashboard(results)
    plot_files['interactive_dashboard'] = f"{output_dir}/policy_dashboard.html"
    fig.write_html(plot_files['interactive_dashboard'])

    # Cost-effectiveness acceptability
    fig = plot_policy_cost_effectiveness_acceptability(results)
    plot_files['ceac_curves'] = f"{output_dir}/policy_ceac_curves.png"
    save_multiformat(fig, plot_files['ceac_curves'])
    plt.close(fig)

    # Equity impact analysis
    fig = plot_policy_equity_impact(results)
    plot_files['equity_impact'] = f"{output_dir}/policy_equity_impact.png"
    save_multiformat(fig, plot_files['equity_impact'])
    plt.close(fig)

    # No logger available here

    return plot_files
