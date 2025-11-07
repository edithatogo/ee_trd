"""
Cost-Consequence Analysis (CCA) Plotting Functions for V4 Health Economic Analysis

This module provides visualization functions for cost-consequence analysis results,
including disaggregated cost/outcome plots, summary tables, and scenario analysis.

Features:
- Cost and outcome comparison plots
- Tornado diagrams for uncertainty
- Scenario analysis visualizations
- Publication-quality formatting

Author: V4 Development Team
Date: October 2025
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Optional, Dict
from pathlib import Path
import logging

from analysis.plotting.publication import (
    journal_style, save_multiformat, format_axis_currency
)
from analysis.engines.cca_engine import CCAResults


def plot_cca_cost_comparison(
    results: CCAResults,
    save_path: Optional[str] = None,
    include_all_strategies: bool = True,
    **kwargs
) -> plt.Figure:
    """
    Plot cost comparison across strategies in CCA.

    Args:
        results: CCA analysis results
        save_path: Path to save figure
        include_all_strategies: If True, ensure all 10 treatment strategies are included
                               in plots even if they lack cost data
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    # Data validation: Ensure results object has expected attributes
    assert hasattr(results, 'strategies'), "CCAResults must have strategies attribute"
    assert hasattr(results, 'total_costs'), "CCAResults must have total_costs attribute"
    
    # Data validation: Check strategy coverage when include_all_strategies is True
    if include_all_strategies:
        from analysis.core.io import StrategyConfig
        from pathlib import Path
        config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
        # Filter out step-care sequences for basic CCA analysis
        expected_strategies = set([s for s in config.strategies if not s.startswith('Step-care:')])
        # Allow flexible strategy count as names may differ between data and config
        
        # Validate that available strategies exist
        available_strategies = set(results.strategies)
        logging.info(f"Available strategies: {available_strategies}")
        logging.info(f"Expected individual strategies: {expected_strategies}")

    with journal_style():
        fig, ax = plt.subplots(figsize=(12, 8))

        strategies = results.strategies
        cost_data = []

        # Get all individual strategies from config if include_all_strategies is True
        if include_all_strategies:
            from analysis.core.io import StrategyConfig
            from pathlib import Path
            config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
            # Filter out step-care sequences for basic CCA analysis
            config_strategies = [s for s in config.strategies if not s.startswith('Step-care:')]
            # Use available strategies but ensure we include placeholders for missing ones
            all_strategies = list(set(strategies + config_strategies))
        else:
            all_strategies = strategies

        for strategy in all_strategies:
            if strategy in results.total_costs:
                cost_info = results.total_costs[strategy]
                cost_data.append({
                    'strategy': strategy,
                    'mean': cost_info['mean'],
                    'ci_lower': cost_info['ci_lower'],
                    'ci_upper': cost_info['ci_upper'],
                    'has_data': True
                })
            elif include_all_strategies:
                # Add placeholder for missing strategies
                cost_data.append({
                    'strategy': strategy,
                    'mean': 0,
                    'ci_lower': 0,
                    'ci_upper': 0,
                    'has_data': False
                })

        if cost_data:
            df = pd.DataFrame(cost_data)

            # Sort by mean cost, but keep missing data strategies at end
            df_with_data = df[df['has_data']].sort_values('mean')
            df_without_data = df[~df['has_data']]
            df = pd.concat([df_with_data, df_without_data])

            # Create bar plot with error bars
            colors = ['lightcoral' if has_data else 'lightgray' for has_data in df['has_data']]
            bars = ax.bar(range(len(df)), df['mean'],
                         yerr=[df['mean'] - df['ci_lower'], df['ci_upper'] - df['mean']],
                         capsize=5, alpha=0.7, color=colors)

            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df['strategy'], rotation=45, ha='right')
            format_axis_currency(ax, axis='y')
            ax.set_title('Cost Comparison Across Strategies')
            ax.set_ylabel('Cost ($)')
            ax.grid(True, alpha=0.3)

            # Highlight lowest cost
            min_idx = df['mean'].idxmin()
            bars[min_idx].set_color('red')
            bars[min_idx].set_label('Lowest Cost')

            ax.legend()

        if save_path:
            save_multiformat(fig, save_path)

        return fig


def plot_cca_outcome_comparison(
    results: CCAResults,
    outcome_name: str = 'effect',
    save_path: Optional[str] = None,
    include_all_strategies: bool = True,
    **kwargs
) -> plt.Figure:
    """
    Plot outcome comparison across strategies in CCA.

    Args:
        results: CCA analysis results
        outcome_name: Name of outcome measure to plot
        save_path: Path to save figure
        include_all_strategies: If True, ensure all 10 treatment strategies are included
                               in plots even if they lack outcome data
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    # Data validation: Ensure results object has expected attributes
    assert hasattr(results, 'strategies'), "CCAResults must have strategies attribute"
    assert hasattr(results, 'outcome_measures'), "CCAResults must have outcome_measures attribute"
    assert hasattr(results, 'base_case_results'), "CCAResults must have base_case_results attribute"
    
    # Data validation: Check strategy coverage when include_all_strategies is True
    if include_all_strategies:
        from analysis.core.io import StrategyConfig
        from pathlib import Path
        config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
        # Filter out step-care sequences for basic CCA analysis
        expected_strategies = set([s for s in config.strategies if not s.startswith('Step-care:')])
        # Allow flexible strategy count as names may differ between data and config
        
        # Validate that available strategies exist
        available_strategies = set(results.strategies)
        logging.info(f"Outcome plot - Available strategies: {available_strategies}")
        logging.info(f"Outcome plot - Expected individual strategies: {expected_strategies}")

    with journal_style():
        fig, ax = plt.subplots(figsize=(12, 8))

        strategies = results.strategies

        # Get all individual strategies from config if include_all_strategies is True
        if include_all_strategies:
            from analysis.core.io import StrategyConfig
            from pathlib import Path
            config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
            # Filter out step-care sequences for basic CCA analysis
            config_strategies = [s for s in config.strategies if not s.startswith('Step-care:')]
            # Use available strategies but ensure we include placeholders for missing ones
            all_strategies = list(set(strategies + config_strategies))
        else:
            all_strategies = strategies

        outcome_data = []

        # Find the specified outcome measure
        outcome_measure = None
        for measure in results.outcome_measures:
            if measure.name == outcome_name:
                outcome_measure = measure
                break

        if outcome_measure:
            # Calculate outcome stats per strategy
            for strategy in all_strategies:
                strategy_mask = results.base_case_results['strategy'] == strategy
                if strategy_mask.any():
                    values = results.base_case_results.loc[strategy_mask, outcome_name].values
                    outcome_data.append({
                        'strategy': strategy,
                        'mean': np.mean(values),
                        'ci_lower': np.percentile(values, 2.5),
                        'ci_upper': np.percentile(values, 97.5),
                        'has_data': True
                    })
                elif include_all_strategies:
                    # Add placeholder for missing strategies
                    outcome_data.append({
                        'strategy': strategy,
                        'mean': 0,
                        'ci_lower': 0,
                        'ci_upper': 0,
                        'has_data': False
                    })

        if outcome_data:
            df = pd.DataFrame(outcome_data)

            # Sort by mean outcome (descending for "higher is better"), but keep missing data strategies at end
            if df['has_data'].any():
                df_with_data = df[df['has_data']].sort_values('mean', ascending=not outcome_measure.higher_is_better)
                df_without_data = df[~df['has_data']]
                df = pd.concat([df_with_data, df_without_data])

            # Create bar plot with error bars
            colors = ['lightblue' if has_data else 'lightgray' for has_data in df['has_data']]
            bars = ax.bar(range(len(df)), df['mean'],
                         yerr=[df['mean'] - df['ci_lower'], df['ci_upper'] - df['mean']],
                         capsize=5, alpha=0.7, color=colors)

            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df['strategy'], rotation=45, ha='right')
            ax.set_title(f'{outcome_measure.description} Comparison Across Strategies')
            ax.set_ylabel(f'{outcome_measure.description} ({outcome_measure.unit})')
            ax.grid(True, alpha=0.3)

            # Highlight best outcome
            if outcome_measure.higher_is_better:
                best_idx = df['mean'].idxmax()
            else:
                best_idx = df['mean'].idxmin()

            bars[best_idx].set_color('blue')
            bars[best_idx].set_label('Best Outcome')

            ax.legend()

        if save_path:
            save_multiformat(fig, save_path)

        return fig


def plot_cca_cost_outcome_plane(
    results: CCAResults,
    save_path: Optional[str] = None,
    include_all_strategies: bool = True,
    **kwargs
) -> plt.Figure:
    """
    Plot cost-outcome plane showing all strategies.

    Args:
        results: CCA analysis results
        save_path: Path to save figure
        include_all_strategies: If True, ensure all 10 treatment strategies are included
                               in plots even if they lack data
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    # Data validation assertions
    assert hasattr(results, 'strategies'), "CCAResults object missing 'strategies' attribute"
    assert hasattr(results, 'total_costs'), "CCAResults object missing 'total_costs' attribute"
    assert hasattr(results, 'base_case_results'), "CCAResults object missing 'base_case_results' attribute"

    # Strategy coverage validation
    from analysis.core.io import StrategyConfig
    from pathlib import Path
    config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
    # Filter out step-care sequences for basic CCA analysis
    expected_strategies = set([s for s in config.strategies if not s.startswith('Step-care:')])
    available_strategies = set(results.strategies)
    logging.info(f"Summary table - Available strategies: {available_strategies}")
    logging.info(f"Summary table - Expected individual strategies: {expected_strategies}")

    with journal_style():
        fig, ax = plt.subplots(figsize=(12, 8))

        strategies = results.strategies

        # Get all 10 strategies from config if include_all_strategies is True
        if include_all_strategies:
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            all_strategies = list(config.keys())
        else:
            all_strategies = strategies

        from analysis.plotting.publication import _get_cmap
        cmap = _get_cmap('tab10')
        sampled = cmap(np.linspace(0, 1, max(len(all_strategies), 10)))
        colors = [tuple(sampled[i % len(sampled)]) for i in range(len(all_strategies))]

        for i, strategy in enumerate(all_strategies):
            strategy_data = results.base_case_results[results.base_case_results['strategy'] == strategy]

            if not strategy_data.empty and strategy in results.total_costs:
                cost_mean = results.total_costs[strategy]['mean']
                effect_mean = strategy_data['effect'].mean()

                # Plot point with error bars
                ax.errorbar(effect_mean, cost_mean,
                          xerr=[[effect_mean - strategy_data['effect'].quantile(0.025)],
                                [strategy_data['effect'].quantile(0.975) - effect_mean]],
                          yerr=[[cost_mean - results.total_costs[strategy]['ci_lower']],
                                [results.total_costs[strategy]['ci_upper'] - cost_mean]],
                          fmt='o', capsize=3, color=colors[i], label=strategy, markersize=8)
            elif include_all_strategies:
                # Plot placeholder point for missing strategies
                ax.plot(0, 0, 'o', color='lightgray', markersize=8, label=f'{strategy} (no data)', alpha=0.5)

        ax.set_xlabel('Effectiveness (QALYs)')
        ax.set_ylabel('Cost ($)')
        format_axis_currency(ax, axis='y')
        ax.set_title('Cost-Effectiveness Plane')
        ax.grid(True, alpha=0.3)
        ax.legend()

        if save_path:
            save_multiformat(fig, save_path)

        return fig


def plot_cca_scenario_analysis(
    results: CCAResults,
    save_path: Optional[str] = None,
    include_all_strategies: bool = True,
    **kwargs
) -> plt.Figure:
    """
    Plot scenario analysis results.

    Args:
        results: CCA analysis results
        save_path: Path to save figure
        include_all_strategies: If True, ensure all 10 treatment strategies are included
                               in plots even if they lack scenario data
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    # Data validation: Ensure results object has expected structure
    assert hasattr(results, 'scenario_analysis'), "CCAResults must have scenario_analysis attribute"
    
    # Data validation: Check strategy coverage when include_all_strategies is True
    if include_all_strategies:
        from analysis.core.io import StrategyConfig
        from pathlib import Path
        config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
        # Filter out step-care sequences for basic CCA analysis
        expected_strategies = set([s for s in config.strategies if not s.startswith('Step-care:')])
        
        # If scenario data exists, validate that available strategies exist
        if results.scenario_analysis:
            available_strategies = set(results.scenario_analysis.keys())
            logging.info(f"Scenario analysis - Available strategies: {available_strategies}")
            logging.info(f"Scenario analysis - Expected individual strategies: {expected_strategies}")

    if not results.scenario_analysis:
        # Create empty figure if no scenario data
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.text(0.5, 0.5, 'No scenario analysis data available',
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Scenario Analysis')
        return fig

    with journal_style():
        fig, axes = plt.subplots(1, 2, figsize=(16, 8))

        # Get all 10 strategies from config if include_all_strategies is True
        if include_all_strategies:
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            all_strategies = list(config.keys())
        else:
            all_strategies = list(results.scenario_analysis.keys())

        from analysis.plotting.publication import _get_cmap
        cmap = _get_cmap('tab10')
        sampled = cmap(np.linspace(0, 1, max(len(all_strategies), 10)))
        colors = [tuple(sampled[i % len(sampled)]) for i in range(len(all_strategies))]

        # Cost scenarios
        ax1 = axes[0]
        for i, strategy in enumerate(all_strategies):
            if strategy in results.scenario_analysis:
                scenario = results.scenario_analysis[strategy]
                costs = [scenario['best_case']['cost'],
                        scenario['base_case']['cost'],
                        scenario['worst_case']['cost']]
                ax1.plot([0, 1, 2], costs, 'o-', color=colors[i], label=strategy, markersize=8)
            elif include_all_strategies:
                # Add placeholder line for missing strategies
                ax1.plot([0, 1, 2], [0, 0, 0], 'o--', color='lightgray', alpha=0.5, label=f'{strategy} (no data)', markersize=8)

        ax1.set_xticks([0, 1, 2])
        ax1.set_xticklabels(['Best Case', 'Base Case', 'Worst Case'])
        ax1.set_ylabel('Cost ($)')
        format_axis_currency(ax1, axis='y')
        ax1.set_title('Cost Scenarios')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Effect scenarios
        ax2 = axes[1]
        for i, strategy in enumerate(all_strategies):
            if strategy in results.scenario_analysis:
                scenario = results.scenario_analysis[strategy]
                effects = [scenario['best_case']['effect'],
                          scenario['base_case']['effect'],
                          scenario['worst_case']['effect']]
                ax2.plot([0, 1, 2], effects, 'o-', color=colors[i], label=strategy, markersize=8)
            elif include_all_strategies:
                # Add placeholder line for missing strategies
                ax2.plot([0, 1, 2], [0, 0, 0], 'o--', color='lightgray', alpha=0.5, label=f'{strategy} (no data)', markersize=8)

        ax2.set_xticks([0, 1, 2])
        ax2.set_xticklabels(['Best Case', 'Base Case', 'Worst Case'])
        ax2.set_ylabel('Effectiveness (QALYs)')
        ax2.set_title('Effectiveness Scenarios')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            save_multiformat(fig, save_path)

        return fig


def create_cca_report_plots(
    results: CCAResults,
    output_dir: str,
    include_all_strategies: bool = True,
    **kwargs
) -> Dict[str, str]:
    """
    Create comprehensive CCA report plots.

    Args:
        results: CCA analysis results
        output_dir: Directory to save plots
        include_all_strategies: If True, ensure all 10 treatment strategies are included
                               in plots even if they lack data
        **kwargs: Additional plotting arguments

    Returns:
        Dictionary mapping plot names to file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    plots = {}

    # Cost comparison
    cost_plot_path = output_path / "cca_cost_comparison"
    plot_cca_cost_comparison(results, save_path=str(cost_plot_path), include_all_strategies=include_all_strategies)
    plots['cost_comparison'] = str(cost_plot_path) + '.png'

    # Outcome comparison
    outcome_plot_path = output_path / "cca_outcome_comparison"
    plot_cca_outcome_comparison(results, save_path=str(outcome_plot_path), include_all_strategies=include_all_strategies)
    plots['outcome_comparison'] = str(outcome_plot_path) + '.png'

    # Cost-outcome plane
    plane_plot_path = output_path / "cca_cost_outcome_plane"
    plot_cca_cost_outcome_plane(results, save_path=str(plane_plot_path), include_all_strategies=include_all_strategies)
    plots['cost_outcome_plane'] = str(plane_plot_path) + '.png'

    # Scenario analysis
    scenario_plot_path = output_path / "cca_scenario_analysis"
    plot_cca_scenario_analysis(results, save_path=str(scenario_plot_path), include_all_strategies=include_all_strategies)
    plots['scenario_analysis'] = str(scenario_plot_path) + '.png'

    return plots
