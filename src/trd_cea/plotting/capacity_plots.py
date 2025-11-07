"""
V4 Capacity Constraints and Implementation Features Plotting

Provides publication-quality visualizations for capacity constraints analysis,
implementation costs, and health system capacity modeling.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Optional
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..engines.capacity_constraints_engine import CapacityConstraintResult, ImplementationCostResult
from ..engines.implementation_costs_engine import ImplementationCostResult
from ..engines.external_validation_engine import ExternalValidationResults


def plot_waiting_time_distributions(
    capacity_result: CapacityConstraintResult,
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot waiting time distributions across capacity scenarios.
    
    Args:
        capacity_result: Capacity constraint analysis results
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure object
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle("Waiting Time Analysis by Treatment Strategy", fontsize=16, fontweight='bold')
    
    waiting_data = capacity_result.waiting_times
    
    # Mean waiting times by capacity multiplier
    ax = axes[0, 0]
    pivot_mean = waiting_data.pivot(index='capacity_multiplier', columns='strategy', values='mean_waiting_days')
    pivot_mean.plot(ax=ax, marker='o', linewidth=2)
    ax.set_title('Mean Waiting Times by Capacity Level')
    ax.set_xlabel('Capacity Multiplier')
    ax.set_ylabel('Mean Waiting Time (Days)')
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 95th percentile waiting times
    ax = axes[0, 1]
    pivot_p95 = waiting_data.pivot(index='capacity_multiplier', columns='strategy', values='p95_waiting_days')
    pivot_p95.plot(ax=ax, marker='s', linewidth=2)
    ax.set_title('95th Percentile Waiting Times')
    ax.set_xlabel('Capacity Multiplier')
    ax.set_ylabel('95th Percentile Waiting Time (Days)')
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Utilization rates
    ax = axes[1, 0]
    util_data = capacity_result.utilization_rates
    pivot_util = util_data.pivot(index='capacity_multiplier', columns='strategy', values='utilization_rate')
    pivot_util.plot(ax=ax, marker='^', linewidth=2)
    ax.axhline(y=0.8, color='red', linestyle='--', alpha=0.7, label='High Utilization Threshold')
    ax.axhline(y=0.6, color='orange', linestyle='--', alpha=0.7, label='Medium Utilization Threshold')
    ax.set_title('Resource Utilization Rates')
    ax.set_xlabel('Capacity Multiplier')
    ax.set_ylabel('Utilization Rate')
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Bottleneck analysis
    ax = axes[1, 1]
    bottleneck_data = capacity_result.bottleneck_analysis
    colors = {'Low': 'green', 'Medium': 'orange', 'High': 'red', 'Critical': 'darkred'}
    bottleneck_colors = [colors.get(level, 'gray') for level in bottleneck_data['bottleneck_indicator']]
    
    _bars = ax.bar(bottleneck_data['strategy'], bottleneck_data['utilization_rate'], 
                   color=bottleneck_colors, alpha=0.7)
    ax.set_title('Bottleneck Analysis')
    ax.set_xlabel('Treatment Strategy')
    ax.set_ylabel('Maximum Utilization Rate')
    ax.tick_params(axis='x', rotation=45)
    
    # Add legend
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.7) 
                      for color in colors.values()]
    ax.legend(legend_elements, colors.keys(), title='Bottleneck Level', 
              bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_implementation_cost_breakdown(
    implementation_result: ImplementationCostResult,
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot implementation cost breakdown by category and strategy.
    
    Args:
        implementation_result: Implementation cost analysis results
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure object
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle("Implementation Cost Analysis", fontsize=16, fontweight='bold')
    
    # Startup costs
    ax = axes[0, 0]
    startup_data = implementation_result.startup_costs
    strategies = startup_data['strategy']
    equipment = startup_data['equipment_cost']
    adoption = startup_data['adoption_cost']
    
    ax.bar(strategies, equipment, label='Equipment', alpha=0.7)
    ax.bar(strategies, adoption, bottom=equipment, label='Adoption', alpha=0.7)
    ax.set_title('Startup Costs by Strategy')
    ax.set_ylabel('Cost ($)')
    ax.tick_params(axis='x', rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Operational costs
    ax = axes[0, 1]
    operational_data = implementation_result.operational_costs
    supplies = operational_data['supplies_cost']
    monitoring = operational_data['monitoring_cost']
    
    ax.bar(strategies, supplies, label='Supplies', alpha=0.7)
    ax.bar(strategies, monitoring, bottom=supplies, label='Monitoring', alpha=0.7)
    ax.set_title('Annual Operational Costs')
    ax.set_ylabel('Annual Cost ($)')
    ax.tick_params(axis='x', rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Training costs
    ax = axes[1, 0]
    training_data = implementation_result.training_costs
    training_costs = training_data['training_cost']
    
    _bars = ax.bar(strategies, training_costs, color='skyblue', alpha=0.7)
    ax.set_title('Training Costs by Strategy')
    ax.set_ylabel('Training Cost ($)')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, cost in zip(_bars, training_costs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 100,
                f'${cost:,.0f}', ha='center', va='bottom', fontsize=9)
    
    # Total 5-year costs
    ax = axes[1, 1]
    total_data = implementation_result.total_costs
    total_costs = total_data['total_5year_cost']
    
    _bars = ax.bar(strategies, total_costs, color='lightcoral', alpha=0.7)
    ax.set_title('Total 5-Year Implementation Costs')
    ax.set_ylabel('Total Cost ($)')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, cost in zip(_bars, total_costs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1000,
                f'${cost:,.0f}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_cost_amortization_schedule(
    implementation_result: ImplementationCostResult,
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot cost amortization schedule over time.
    
    Args:
        implementation_result: Implementation cost analysis results
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    amortization_data = implementation_result.cost_amortization
    
    # Group by strategy and plot cumulative costs
    strategies = amortization_data['strategy'].unique()
    from analysis.plotting.publication import _get_cmap
    cmap = _get_cmap('tab10')
    sampled = cmap(np.linspace(0, 1, max(len(strategies), 10)))
    colors = [tuple(sampled[i % len(sampled)]) for i in range(len(strategies))]
    
    for i, strategy in enumerate(strategies):
        strategy_data = amortization_data[amortization_data['strategy'] == strategy]
        cumulative_cost = strategy_data['total_annual_cost'].cumsum()
        years = strategy_data['year']
        
        ax.plot(years, cumulative_cost, marker='o', linewidth=2, 
                label=strategy, color=colors[i])
    
    ax.set_title('Implementation Cost Amortization Schedule', fontsize=14, fontweight='bold')
    ax.set_xlabel('Year')
    ax.set_ylabel('Cumulative Cost ($)')
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add value labels for final year
    for i, strategy in enumerate(strategies):
        strategy_data = amortization_data[amortization_data['strategy'] == strategy]
        final_cost = strategy_data['total_annual_cost'].cumsum().iloc[-1]
        ax.annotate(f'${final_cost:,.0f}', 
                   xy=(5, final_cost), 
                   xytext=(5.1, final_cost),
                   fontsize=9, color=colors[i])
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_breakeven_analysis(
    implementation_result: ImplementationCostResult,
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot breakeven analysis for implementation costs.
    
    Args:
        implementation_result: Implementation cost analysis results
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure object
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("Breakeven Analysis", fontsize=14, fontweight='bold')
    
    breakeven_data = implementation_result.breakeven_analysis
    
    # Breakeven years
    ax = axes[0]
    strategies = breakeven_data['strategy']
    breakeven_years = []
    
    for year in breakeven_data['breakeven_year']:
        if isinstance(year, str) and year.startswith('>'):
            breakeven_years.append(6)  # Beyond 5 years
        else:
            breakeven_years.append(float(year))
    
    colors = ['green' if year <= 3 else 'orange' if year <= 5 else 'red' for year in breakeven_years]
    _bars = ax.bar(strategies, breakeven_years, color=colors, alpha=0.7)
    ax.set_title('Breakeven Timeline')
    ax.set_ylabel('Years to Breakeven')
    ax.set_xlabel('Treatment Strategy')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    
    # Add value labels
    for bar, year in zip(_bars, breakeven_years):
        height = bar.get_height()
        label = f'{year:.1f}' if year < 6 else '>5'
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                label, ha='center', va='bottom', fontsize=9)
    
    # Profitability ratios
    ax = axes[1]
    profitability = breakeven_data['profitability_ratio']
    colors = ['green' if ratio > 2 else 'orange' if ratio > 1 else 'red' for ratio in profitability]
    _bars = ax.bar(strategies, profitability, color=colors, alpha=0.7)
    ax.set_title('Profitability Ratios')
    ax.set_ylabel('Revenue/Cost Ratio')
    ax.set_xlabel('Treatment Strategy')
    ax.tick_params(axis='x', rotation=45)
    ax.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='Breakeven')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Add value labels
    for bar, ratio in zip(_bars, profitability):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{ratio:.2f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def create_interactive_capacity_dashboard(
    capacity_result: CapacityConstraintResult,
    implementation_result: ImplementationCostResult,
    save_path: Optional[Path] = None,
    **kwargs
) -> go.Figure:
    """
    Create interactive dashboard combining capacity and implementation analysis.
    
    Args:
        capacity_result: Capacity constraint analysis results
        implementation_result: Implementation cost analysis results
        save_path: Optional path to save the figure
        
    Returns:
        Plotly figure object
    """
    # Create subplot figure
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Waiting Times by Capacity', 'Utilization Rates', 
                       'Implementation Costs', 'Breakeven Analysis'),
        specs=[[{'type': 'scatter'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'scatter'}]]
    )
    
    # Waiting times plot
    waiting_data = capacity_result.waiting_times
    for strategy in waiting_data['strategy'].unique():
        strategy_data = waiting_data[waiting_data['strategy'] == strategy]
        fig.add_trace(
            go.Scatter(
                x=strategy_data['capacity_multiplier'],
                y=strategy_data['mean_waiting_days'],
                mode='lines+markers',
                name=f'{strategy} - Waiting',
                legendgroup=strategy,
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Utilization rates plot
    util_data = capacity_result.utilization_rates
    for strategy in util_data['strategy'].unique():
        strategy_data = util_data[util_data['strategy'] == strategy]
        fig.add_trace(
            go.Bar(
                x=strategy_data['capacity_multiplier'],
                y=strategy_data['utilization_rate'],
                name=f'{strategy} - Utilization',
                legendgroup=strategy,
                showlegend=False,
                opacity=0.7
            ),
            row=1, col=2
        )
    
    # Implementation costs plot
    cost_data = implementation_result.total_costs
    fig.add_trace(
        go.Bar(
            x=cost_data['strategy'],
            y=cost_data['total_5year_cost'],
            name='Total 5-Year Costs',
            marker_color='lightcoral',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Breakeven analysis plot
    breakeven_data = implementation_result.breakeven_analysis
    breakeven_years = []
    for year in breakeven_data['breakeven_year']:
        if isinstance(year, str) and year.startswith('>'):
            breakeven_years.append(6)
        else:
            breakeven_years.append(float(year))
    
    fig.add_trace(
        go.Scatter(
            x=breakeven_data['strategy'],
            y=breakeven_years,
            mode='markers',
            name='Breakeven Years',
            marker=dict(size=10, color='green'),
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text="Capacity Constraints & Implementation Analysis Dashboard",
        height=800,
        showlegend=True
    )
    
    # Update axes
    fig.update_xaxes(title_text="Capacity Multiplier", row=1, col=1)
    fig.update_yaxes(title_text="Mean Waiting Time (Days)", row=1, col=1)
    fig.update_xaxes(title_text="Capacity Multiplier", row=1, col=2)
    fig.update_yaxes(title_text="Utilization Rate", row=1, col=2)
    fig.update_xaxes(title_text="Strategy", row=2, col=1)
    fig.update_yaxes(title_text="Total Cost ($)", row=2, col=1)
    fig.update_xaxes(title_text="Strategy", row=2, col=2)
    fig.update_yaxes(title_text="Years to Breakeven", row=2, col=2)
    
    if save_path:
        fig.write_html(save_path)
    
    return fig


def plot_detailed_cost_breakdown(
    implementation_result: ImplementationCostResult,
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot detailed cost breakdown by category and component.
    
    Args:
        implementation_result: Implementation cost analysis results
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure object
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle("Detailed Implementation Cost Breakdown", fontsize=16, fontweight='bold')
    
    strategies = implementation_result.startup_costs['strategy']
    
    # Startup costs breakdown
    ax = axes[0, 0]
    startup_data = implementation_result.startup_costs
    components = ['equipment_cost', 'facility_modifications', 'regulatory_costs', 
                 'initial_marketing', 'it_setup']
    labels = ['Equipment', 'Facility Mods', 'Regulatory', 'Marketing', 'IT Setup']
    
    bottom = np.zeros(len(strategies))
    for i, (component, label) in enumerate(zip(components, labels)):
        values = startup_data[component]
        ax.bar(strategies, values, bottom=bottom, label=label, alpha=0.8)
        bottom += values
    
    ax.set_title('Startup Costs Breakdown')
    ax.set_ylabel('Cost ($)')
    ax.tick_params(axis='x', rotation=45)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Training costs breakdown
    ax = axes[0, 1]
    training_data = implementation_result.training_costs
    training_components = ['training_labor_cost', 'materials_cost', 'certification_cost']
    training_labels = ['Labor', 'Materials', 'Certification']
    
    bottom = np.zeros(len(strategies))
    for i, (component, label) in enumerate(zip(training_components, training_labels)):
        values = training_data[component]
        ax.bar(strategies, values, bottom=bottom, label=label, alpha=0.8)
        bottom += values
    
    ax.set_title('Training Costs Breakdown')
    ax.set_ylabel('Cost ($)')
    ax.tick_params(axis='x', rotation=45)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Operational costs breakdown
    ax = axes[0, 2]
    operational_data = implementation_result.operational_costs
    operational_components = ['supplies_cost', 'monitoring_cost', 'maintenance_annual', 
                             'quality_assurance', 'administrative_overhead']
    operational_labels = ['Supplies', 'Monitoring', 'Maintenance', 'QA', 'Admin']
    
    bottom = np.zeros(len(strategies))
    for i, (component, label) in enumerate(zip(operational_components, operational_labels)):
        values = operational_data[component]
        ax.bar(strategies, values, bottom=bottom, label=label, alpha=0.8)
        bottom += values
    
    ax.set_title('Annual Operational Costs')
    ax.set_ylabel('Annual Cost ($)')
    ax.tick_params(axis='x', rotation=45)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Adoption costs breakdown
    ax = axes[1, 0]
    adoption_data = implementation_result.adoption_costs
    adoption_components = ['patient_education', 'outreach_marketing', 'care_coordination', 
                          'transport_assistance', 'retention_programs']
    adoption_labels = ['Education', 'Outreach', 'Coordination', 'Transport', 'Retention']
    
    bottom = np.zeros(len(strategies))
    for i, (component, label) in enumerate(zip(adoption_components, adoption_labels)):
        values = adoption_data[component]
        ax.bar(strategies, values, bottom=bottom, label=label, alpha=0.8)
        bottom += values
    
    ax.set_title('Annual Adoption Costs')
    ax.set_ylabel('Annual Cost ($)')
    ax.tick_params(axis='x', rotation=45)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Cost per patient
    ax = axes[1, 1]
    cost_per_patient = implementation_result.total_costs['cost_per_patient_year1']
    _bars = ax.bar(strategies, cost_per_patient, color='lightblue', alpha=0.7)
    ax.set_title('Cost per Patient (Year 1)')
    ax.set_ylabel('Cost per Patient ($)')
    ax.tick_params(axis='x', rotation=45)
    
    # Add value labels
    for bar, cost in zip(_bars, cost_per_patient):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 50,
                f'${cost:.0f}', ha='center', va='bottom', fontsize=9)
    
    # Cost-effectiveness
    ax = axes[1, 2]
    ce_data = implementation_result.cost_effectiveness
    ce_ratios = ce_data['cost_per_qaly']
    _bars = ax.bar(strategies, ce_ratios, color='lightgreen', alpha=0.7)
    ax.set_title('Cost per QALY')
    ax.set_ylabel('Cost per QALY ($)')
    ax.tick_params(axis='x', rotation=45)
    
    # Add value labels
    for bar, ce in zip(_bars, ce_ratios):
        height = bar.get_height()
        if ce == float('inf'):
            label = '∞'
        else:
            label = f'${ce:,.0f}'
        ax.text(bar.get_x() + bar.get_width()/2., height + 1000,
                label, ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_cost_sensitivity_analysis(
    implementation_result: ImplementationCostResult,
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot cost sensitivity analysis results.
    
    Args:
        implementation_result: Implementation cost analysis results
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure object
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle("Cost Sensitivity Analysis", fontsize=16, fontweight='bold')
    
    sensitivity_data = implementation_result.sensitivity_analysis
    
    # Tornado diagram for each strategy
    strategies = sensitivity_data['strategy'].unique()
    
    for i, strategy in enumerate(strategies[:4]):  # Show first 4 strategies
        ax = axes[i // 2, i % 2]
        
        strategy_data = sensitivity_data[sensitivity_data['strategy'] == strategy]
        
        # Sort by sensitivity range
        strategy_data = strategy_data.sort_values('sensitivity_range', ascending=True)
        
        parameters = strategy_data['parameter']
        low_changes = strategy_data['low_change_percent']
        high_changes = strategy_data['high_change_percent']
        
        # Create tornado bars
        y_pos = np.arange(len(parameters))
        
        ax.barh(y_pos, high_changes - low_changes, left=low_changes, 
                color='lightcoral', alpha=0.7, label='Sensitivity Range')
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels([p.replace('_', ' ').title() for p in parameters])
        ax.set_xlabel('Cost Change (%)')
        ax.set_title(f'{strategy} Sensitivity')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_breakeven_timeline(
    implementation_result: ImplementationCostResult,
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot breakeven timeline and profitability analysis.
    
    Args:
        implementation_result: Implementation cost analysis results
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure object
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle("Breakeven and Profitability Analysis", fontsize=16, fontweight='bold')
    
    breakeven_data = implementation_result.breakeven_analysis
    
    # Breakeven timeline
    ax = axes[0, 0]
    strategies = breakeven_data['strategy']
    breakeven_years = []
    
    for year in breakeven_data['breakeven_year']:
        if isinstance(year, str) and year.startswith('>'):
            breakeven_years.append(6)  # Beyond 5 years
        else:
            breakeven_years.append(float(year))
    
    colors = ['green' if year <= 2 else 'orange' if year <= 4 else 'red' for year in breakeven_years]
    _bars = ax.bar(strategies, breakeven_years, color=colors, alpha=0.7)
    ax.set_title('Breakeven Timeline')
    ax.set_ylabel('Years to Breakeven')
    ax.set_xlabel('Treatment Strategy')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    
    # Add value labels
    for bar, year in zip(_bars, breakeven_years):
        height = bar.get_height()
        label = f'{year:.1f}' if year < 6 else '>5'
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                label, ha='center', va='bottom', fontsize=9)
    
    # Annual profit/loss
    ax = axes[0, 1]
    annual_profits = breakeven_data['annual_profit']
    colors = ['green' if profit > 0 else 'red' for profit in annual_profits]
    _bars = ax.bar(strategies, annual_profits, color=colors, alpha=0.7)
    ax.set_title('Annual Profit/Loss')
    ax.set_ylabel('Annual Profit ($)')
    ax.set_xlabel('Treatment Strategy')
    ax.tick_params(axis='x', rotation=45)
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.7)
    ax.grid(True, alpha=0.3)
    
    # Profitability ratios
    ax = axes[1, 0]
    profitability = breakeven_data['profitability_ratio']
    colors = ['green' if ratio > 1.5 else 'orange' if ratio > 1 else 'red' for ratio in profitability]
    _bars = ax.bar(strategies, profitability, color=colors, alpha=0.7)
    ax.set_title('Profitability Ratios')
    ax.set_ylabel('Revenue/Cost Ratio')
    ax.set_xlabel('Treatment Strategy')
    ax.tick_params(axis='x', rotation=45)
    ax.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='Breakeven')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Payback period
    ax = axes[1, 1]
    payback_periods = breakeven_data['payback_period_years']
    colors = ['green' if period <= 3 else 'orange' if period <= 5 else 'red' for period in payback_periods]
    _bars = ax.bar(strategies, payback_periods, color=colors, alpha=0.7)
    ax.set_title('Payback Period')
    ax.set_ylabel('Payback Period (Years)')
    ax.set_xlabel('Treatment Strategy')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    
    # Add value labels
    for bar, period in zip(_bars, payback_periods):
        height = bar.get_height()
        if period == float('inf'):
            label = '∞'
        else:
            label = f'{period:.1f}'
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                label, ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


# External Validation Plotting Functions
# ======================================

def plot_calibration_curve(
    validation_results: 'ExternalValidationResults',
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot calibration curve showing predicted vs observed values.

    Args:
        validation_results: External validation results
        save_path: Optional path to save the figure

    Returns:
        Matplotlib figure object
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    calibration_data = validation_results.calibration_data

    # Scatter plot of predicted vs observed
    ax.scatter(calibration_data['observed_mean'], calibration_data['predicted_mean'],
              alpha=0.7, s=50, edgecolors='black', linewidth=0.5)

    # Perfect calibration line
    min_val = min(calibration_data['observed_mean'].min(), calibration_data['predicted_mean'].min())
    max_val = max(calibration_data['observed_mean'].max(), calibration_data['predicted_mean'].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.7, label='Perfect Calibration')

    # Calibration regression line
    slope = validation_results.validation_metrics.calibration_slope
    intercept = validation_results.validation_metrics.calibration_intercept
    x_range = np.linspace(min_val, max_val, 100)
    y_range = slope * x_range + intercept
    ax.plot(x_range, y_range, 'b-', alpha=0.7, label=f'Calibration Fit (slope={slope:.3f})')

    ax.set_xlabel('Observed Mean Effect', fontsize=12)
    ax.set_ylabel('Predicted Mean Effect', fontsize=12)
    ax.set_title('Model Calibration: Predicted vs Observed Effects', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Add strategy labels
    for idx, row in calibration_data.iterrows():
        ax.annotate(row['strategy'],
                   (row['observed_mean'], row['predicted_mean']),
                   xytext=(5, 5), textcoords='offset points', fontsize=8)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def plot_residuals_analysis(
    validation_results: 'ExternalValidationResults',
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot residuals analysis for model diagnostics.

    Args:
        validation_results: External validation results
        save_path: Optional path to save the figure

    Returns:
        Matplotlib figure object
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Model Residuals Analysis', fontsize=16, fontweight='bold')

    residuals = validation_results.model_diagnostics.get('residuals', [])

    if not residuals:
        # No residuals data available
        for ax in axes.flat:
            ax.text(0.5, 0.5, 'No residuals data available',
                   ha='center', va='center', transform=ax.transAxes)
        return fig

    residuals = np.array(residuals)

    # Residuals histogram
    ax = axes[0, 0]
    ax.hist(residuals, bins=30, alpha=0.7, edgecolor='black')
    ax.axvline(np.mean(residuals), color='red', linestyle='--', alpha=0.7,
              label=f'Mean: {np.mean(residuals):.3f}')
    ax.set_xlabel('Residuals')
    ax.set_ylabel('Frequency')
    ax.set_title('Residuals Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Q-Q plot
    ax = axes[0, 1]
    stats.probplot(residuals, dist="norm", plot=ax)
    ax.set_title('Q-Q Plot (Normality Check)')
    ax.grid(True, alpha=0.3)

    # Residuals vs fitted values (simplified)
    ax = axes[1, 0]
    # Since we don't have fitted values, show residuals over index
    ax.scatter(range(len(residuals)), residuals, alpha=0.6)
    ax.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel('Observation Index')
    ax.set_ylabel('Residuals')
    ax.set_title('Residuals vs Observation Index')
    ax.grid(True, alpha=0.3)

    # Residuals autocorrelation (simplified lag plot)
    ax = axes[1, 1]
    if len(residuals) > 1:
        ax.scatter(residuals[:-1], residuals[1:], alpha=0.6)
        min_val = min(residuals.min(), residuals[:-1].min(), residuals[1:].min())
        max_val = max(residuals.max(), residuals[:-1].max(), residuals[1:].max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.7)
    ax.set_xlabel('Residuals[t]')
    ax.set_ylabel('Residuals[t+1]')
    ax.set_title('Residuals Lag Plot')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def plot_cross_validation_results(
    validation_results: 'ExternalValidationResults',
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot cross-validation results and performance metrics.

    Args:
        validation_results: External validation results
        save_path: Optional path to save the figure

    Returns:
        Matplotlib figure object
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Cross-Validation Analysis', fontsize=16, fontweight='bold')

    cv_results = validation_results.cross_validation_results

    if cv_results.empty:
        # No CV results available
        for ax in axes.flat:
            ax.text(0.5, 0.5, 'No cross-validation data available',
                   ha='center', va='center', transform=ax.transAxes)
        return fig

    # CV scores by fold
    ax = axes[0]
    folds = cv_results['fold']
    scores = cv_results['score']
    ax.bar(folds, scores, alpha=0.7, edgecolor='black')
    ax.axhline(y=validation_results.validation_metrics.cv_mean,
              color='red', linestyle='--', alpha=0.7,
              label=f'Mean CV Score: {validation_results.validation_metrics.cv_mean:.3f}')
    ax.set_xlabel('Fold')
    ax.set_ylabel('Cross-Validation Score')
    ax.set_title('CV Scores by Fold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # CV score distribution
    ax = axes[1]
    cv_scores = validation_results.validation_metrics.cv_scores
    ax.hist(cv_scores, bins=10, alpha=0.7, edgecolor='black')
    ax.axvline(np.mean(cv_scores), color='red', linestyle='--', alpha=0.7,
              label=f'Mean: {np.mean(cv_scores):.3f}')
    ax.axvline(np.mean(cv_scores) - np.std(cv_scores), color='orange', linestyle=':', alpha=0.7,
              label=f'±1 SD: {np.std(cv_scores):.3f}')
    ax.axvline(np.mean(cv_scores) + np.std(cv_scores), color='orange', linestyle=':', alpha=0.7)
    ax.set_xlabel('Cross-Validation Score')
    ax.set_ylabel('Frequency')
    ax.set_title('CV Score Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def plot_posterior_predictive_checks(
    validation_results: 'ExternalValidationResults',
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot posterior predictive check results.

    Args:
        validation_results: External validation results
        save_path: Optional path to save the figure

    Returns:
        Matplotlib figure object
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    ppc_data = validation_results.predictive_checks

    if ppc_data.empty:
        ax.text(0.5, 0.5, 'No posterior predictive check data available',
               ha='center', va='center', transform=ax.transAxes)
        return fig

    # Plot p-values for each test statistic
    statistics = ppc_data['statistic']
    p_values = ppc_data['p_value']

    _bars = ax.bar(statistics, p_values, alpha=0.7, edgecolor='black')

    # Add reference lines
    ax.axhline(y=0.05, color='red', linestyle='--', alpha=0.7, label='α = 0.05')
    ax.axhline(y=0.95, color='red', linestyle='--', alpha=0.7)

    # Color bars based on p-value range
    for bar, p_val in zip(_bars, p_values):
        if 0.05 <= p_val <= 0.95:
            bar.set_color('lightgreen')  # Good p-value
        else:
            bar.set_color('lightcoral')  # Extreme p-value

    ax.set_xlabel('Test Statistic')
    ax.set_ylabel('Bayesian p-value')
    ax.set_title('Posterior Predictive Checks', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add value labels
    for bar, p_val in zip(_bars, p_values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{p_val:.3f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def plot_validation_summary_dashboard(
    validation_results: 'ExternalValidationResults',
    save_path: Optional[Path] = None,
    **kwargs
) -> plt.Figure:
    """
    Create a comprehensive validation summary dashboard.

    Args:
        validation_results: External validation results
        save_path: Optional path to save the figure

    Returns:
        Matplotlib figure object
    """
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('External Validation Summary Dashboard', fontsize=18, fontweight='bold')

    # Create subplot grid
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

    # 1. Goodness-of-fit metrics
    ax1 = fig.add_subplot(gs[0, 0])
    metrics = validation_results.validation_metrics
    gof_data = {
        'R²': metrics.r_squared,
        'RMSE': metrics.rmse,
        'MAE': metrics.mae
    }
    ax1.bar(gof_data.keys(), gof_data.values(), alpha=0.7, edgecolor='black')
    ax1.set_title('Goodness-of-Fit Metrics', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)

    # 2. Calibration plot
    ax2 = fig.add_subplot(gs[0, 1:3])  # Span columns 1 and 2
    calibration_data = validation_results.calibration_data
    if not calibration_data.empty:
        ax2.scatter(calibration_data['observed_mean'], calibration_data['predicted_mean'],
                   alpha=0.7, s=50, edgecolors='black', linewidth=0.5)
        min_val = min(calibration_data['observed_mean'].min(), calibration_data['predicted_mean'].min())
        max_val = max(calibration_data['observed_mean'].max(), calibration_data['predicted_mean'].max())
        ax2.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.7)
        slope = metrics.calibration_slope
        intercept = metrics.calibration_intercept
        x_range = np.linspace(min_val, max_val, 100)
        y_range = slope * x_range + intercept
        ax2.plot(x_range, y_range, 'b-', alpha=0.7, label=f'Slope: {slope:.3f}')
        ax2.legend()
    ax2.set_title('Model Calibration', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # 3. Cross-validation results
    ax3 = fig.add_subplot(gs[1, 0])
    cv_scores = metrics.cv_scores
    if cv_scores:
        ax3.hist(cv_scores, bins=8, alpha=0.7, edgecolor='black')
        ax3.axvline(np.mean(cv_scores), color='red', linestyle='--', alpha=0.7)
    ax3.set_title('CV Score Distribution', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    # 4. Posterior predictive checks
    ax4 = fig.add_subplot(gs[1, 1])
    ppc_data = validation_results.predictive_checks
    if not ppc_data.empty:
        statistics = ppc_data['statistic']
        p_values = ppc_data['p_value']
        _bars = ax4.bar(range(len(statistics)), p_values, alpha=0.7, edgecolor='black')
        for bar, p_val in zip(_bars, p_values):
            if not (0.05 <= p_val <= 0.95):
                bar.set_color('lightcoral')
        ax4.set_xticks(range(len(statistics)))
        ax4.set_xticklabels(statistics, rotation=45)
    ax4.set_title('PPC p-values', fontsize=12, fontweight='bold')
    ax4.set_ylim(0, 1)
    ax4.grid(True, alpha=0.3)

    # 5. Residuals analysis
    ax5 = fig.add_subplot(gs[1, 2:4])  # Span columns 2 and 3
    residuals = validation_results.model_diagnostics.get('residuals', [])
    if residuals:
        ax5.hist(residuals, bins=20, alpha=0.7, edgecolor='black')
        ax5.axvline(np.mean(residuals), color='red', linestyle='--', alpha=0.7)
    ax5.set_title('Residuals Distribution', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)

    # 6. Validation summary text
    ax6 = fig.add_subplot(gs[2, :4])  # Span all columns
    ax6.axis('off')

    summary = validation_results.validation_summary
    summary_text = f"""
    Validation Summary:
    • Overall Quality: {summary['overall_model_quality']}
    • R² Acceptable: {summary['goodness_of_fit']['r_squared_acceptable']}
    • Calibration Good: {summary['calibration']['slope_close_to_1']}
    • CV Consistent: {summary['cross_validation']['consistent_performance']}
    • PPC Checks Pass: {summary['posterior_predictive_checks']['all_checks_passed']}

    Recommendations:
    {chr(10).join('• ' + rec for rec in summary['recommendations'])}
    """

    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=1', facecolor='lightgray', alpha=0.5))

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig