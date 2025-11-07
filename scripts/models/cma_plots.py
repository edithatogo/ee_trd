"""Cost-Minimization Analysis (CMA) plotting helpers.

This module provides visualization functions for cost-minimization analysis
results, including equivalence testing plots, cost comparison visualizations,
and sensitivity analysis displays. Functions here produce publication-quality
figures used in the CMA reporting pipeline.

Author: V4 Development Team
Date: October 2025
"""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from typing import Optional, Dict
from pathlib import Path

from analysis.plotting.publication import (
    journal_style, save_multiformat, format_axis_currency
)
from analysis.engines.cma_engine import CMAResults


def _build_display_map(config):
    """Build a robust display map for strategy keys.

    - Prefer user-provided labels from config.labels
    - Fall back to V4_THERAPY_ABBREVIATIONS
    - Provide a mapping for placeholder names like "Therapy A", "Therapy B" -> canonical strategies by order
    """
    from analysis.core.io import V4_THERAPY_ABBREVIATIONS

    individual_strategies = [s for s in config.strategies if not s.startswith('Step-care:')]
    # base display map
    display_map = {s: (config.labels.get(s) or V4_THERAPY_ABBREVIATIONS.get(s) or s) for s in individual_strategies}

    # Support common placeholder names like 'Therapy A', 'Therapy B', ... mapping to canonical strategies
    for idx, canonical in enumerate(individual_strategies):
        letter = chr(ord('A') + idx)
        placeholder = f"Therapy {letter}"
        # map both exact and lowercased variants
        display_map.setdefault(placeholder, display_map.get(canonical, canonical))
        display_map.setdefault(placeholder.lower(), display_map.get(canonical, canonical))

    return display_map


def plot_cma_equivalence_tests(
    results: CMAResults,
    save_path: Optional[str] = None,
    include_all_strategies: bool = True,
    **kwargs
) -> Figure:
    """
    Plot equivalence testing results for CMA.

    Args:
        results: CMA analysis results
        save_path: Path to save figure
        include_all_strategies: If True, ensure all 10 treatment strategies are included
                               in plots even if they lack equivalence test data
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    # Data validation assertions
    assert hasattr(results, 'equivalence_tests'), "CMAResults object missing 'equivalence_tests' attribute"

    # Strategy coverage validation
    from analysis.core.io import StrategyConfig
    from pathlib import Path
    config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
    # Build a robust display mapping (includes placeholders -> canonical)
    display_map = _build_display_map(config)
    # Preserve individual strategies list for ordering and missing checks
    individual_strategies = [s for s in config.strategies if not s.startswith('Step-care:')]
    # No logger available here, but this is an info message

    with journal_style():
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Use canonical strategies from config (preserve order)
        all_strategies = individual_strategies.copy()

        # Extract equivalence test data
        equiv_data = []
        tested_pairs = set()

        for test in results.equivalence_tests:
            # Use display labels for pair text
            # Normalize raw keys (some inputs use 'Therapy A' placeholders)
            a_raw = test.strategy_a
            b_raw = test.strategy_b
            a_label = display_map.get(a_raw, display_map.get(a_raw.lower(), a_raw))
            b_label = display_map.get(b_raw, display_map.get(b_raw.lower(), b_raw))
            equiv_data.append({
                'pair': f"{a_label}\nvs\n{b_label}",
                'effect_diff': test.effect_diff,
                'ci_lower': test.effect_diff_ci_lower,
                'ci_upper': test.effect_diff_ci_upper,
                'equivalent': test.equivalent,
                'margin': test.equivalence_margin
            })
            tested_pairs.add(test.strategy_a)
            tested_pairs.add(test.strategy_b)

        equiv_df = pd.DataFrame(equiv_data)

        # If include_all_strategies is True, note missing strategies (no placeholder comparisons)
        if include_all_strategies:
            missing_strategies = set(all_strategies) - tested_pairs
            if missing_strategies:
                # We intentionally do not fabricate pairwise tests; just report missing strategies
                # but ensure display consistency elsewhere via display_map
                pass

        # ------------------ Top-left: Effect difference plot ------------------
        ax = axes[0, 0]
        # Handle None values for untested strategies
        colors = []
        for eq in equiv_df.get('equivalent', []):
            if pd.isna(eq):
                colors.append('gray')  # Untested strategies
            elif eq:
                colors.append('green')  # Equivalent
            else:
                colors.append('red')  # Not equivalent

        _bars = ax.barh(equiv_df.get('pair', []), equiv_df.get('effect_diff', []),
                      color=colors, alpha=0.7)

        # Add error bars only for tested pairs
        if 'equivalent' in equiv_df.columns and equiv_df['equivalent'].notna().any():
            tested_mask = equiv_df['equivalent'].notna()
            ax.errorbar(equiv_df.loc[tested_mask, 'effect_diff'], 
                         equiv_df.loc[tested_mask].index,
                         xerr=[equiv_df.loc[tested_mask, 'effect_diff'] - equiv_df.loc[tested_mask, 'ci_lower'],
                               equiv_df.loc[tested_mask, 'ci_upper'] - equiv_df.loc[tested_mask, 'effect_diff']],
                         fmt='none', color='black', capsize=3)

            # Add equivalence bounds (only if we have tested data)
            margin = equiv_df.loc[tested_mask, 'margin'].iloc[0]
            ax.axvline(-margin, color='blue', linestyle='--', alpha=0.7, label=f'±{margin:.3f} margin')
            ax.axvline(margin, color='blue', linestyle='--', alpha=0.7)

        ax.set_xlabel('Effect difference (QALYs)')
        ax.set_title('Clinical Equivalence Testing: Ketamine vs Electroconvulsive Therapy')
        # Add a small legend for equivalence status
        import matplotlib.patches as mpatches
        legend_patches = [mpatches.Patch(color='green', label='Equivalent'),
                          mpatches.Patch(color='red', label='Not equivalent'),
                          mpatches.Patch(color='gray', label='Untested')]
        ax.legend(handles=legend_patches, loc='lower right', frameon=False)

        # ------------------ Top-right: Equivalence summary pie ------------------
        ax = axes[0, 1]
        tested_equiv = equiv_df['equivalent'].dropna() if 'equivalent' in equiv_df.columns else pd.Series([])
        if not tested_equiv.empty:
            status_counts = tested_equiv.value_counts()
            colors_pie = ['green' if idx else 'red' for idx in status_counts.index]
            wedges, texts, autotexts = ax.pie(status_counts.values,
                                             labels=['Equivalent' if idx else 'Not Equivalent' for idx in status_counts.index],
                                             colors=colors_pie, autopct='%1.1f%%', startangle=90)
            ax.set_title('Equivalence Test Results: Ketamine vs Electroconvulsive Therapy')
        else:
            ax.text(0.5, 0.5, 'No equivalence tests\nperformed',
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Equivalence Test Results: Ketamine vs Electroconvulsive Therapy')

        # Finish layout and optionally save
        plt.tight_layout()

        if save_path:
            save_multiformat(fig, Path(save_path))

        return fig

        # End of equivalence plotting function


def plot_cma_cost_comparison(
    results: CMAResults,
    save_path: Optional[str] = None,
    include_all_strategies: bool = True,
    **kwargs
) -> Figure:
    """
    Plot cost comparison results for CMA.

    Args:
        results: CMA analysis results
        save_path: Path to save figure
        include_all_strategies: If True, ensure all 10 treatment strategies are included
                               in plots even if they lack cost data
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    # Data validation assertions
    assert hasattr(results, 'cost_minimization_results'), "CMAResults object missing 'cost_minimization_results' attribute"

    # Strategy coverage validation and display mapping
    from analysis.core.io import StrategyConfig
    from pathlib import Path
    config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
    display_map = _build_display_map(config)
    # Preserve individual strategies list for ordering and missing checks
    individual_strategies = [s for s in config.strategies if not s.startswith('Step-care:')]

    with journal_style():
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Use canonical strategies from config
        all_strategies = individual_strategies.copy()

        # Cost comparison among equivalent strategies
        ax = axes[0, 0]
        cost_data = results.cost_minimization_results.copy()

        # If include_all_strategies is True, ensure all strategies are included
        if include_all_strategies:
            existing_strategies = set(cost_data['strategy'].unique())
            missing_strategies = set(all_strategies) - existing_strategies
            if missing_strategies:
                # Add placeholder rows for missing strategies
                for strategy in missing_strategies:
                    cost_data = pd.concat([cost_data, pd.DataFrame({
                        'strategy': [strategy],
                        'cost_mean': [0.0],
                        'cost_ci_lower': [0.0],
                        'cost_ci_upper': [0.0],
                        'effect_mean': [0.0],
                        'effect_ci_lower': [0.0],
                        'effect_ci_upper': [0.0],
                        'equivalent_strategies': [[]],
                        'max_cost_savings': [0.0],
                        'min_cost_savings': [0.0],
                        'is_least_costly': [False]
                    })], ignore_index=True)

        # Ensure numeric columns are numeric and sort by cost
        for col in ['cost_mean', 'cost_ci_lower', 'cost_ci_upper', 'effect_mean', 'effect_ci_lower', 'effect_ci_upper']:
            if col in cost_data.columns:
                cost_data[col] = pd.to_numeric(cost_data[col], errors='coerce').fillna(0.0)

        cost_data = cost_data.sort_values('cost_mean')

        # Add display column and colors
        # Normalize and map display names (handle placeholders like 'Therapy A')
        cost_data['display_strategy'] = cost_data['strategy'].apply(lambda s: display_map.get(s, display_map.get(str(s).lower(), s)))
        colors_cost = ['lightblue' if not lc else 'lightgreen' for lc in cost_data.get('is_least_costly', [False] * len(cost_data))]

        _bars = ax.barh(cost_data['display_strategy'], cost_data['cost_mean'], color=colors_cost, alpha=0.7)

        # Add error bars only for strategies with actual data
        valid_data = (cost_data['cost_ci_lower'] != cost_data['cost_ci_upper']) if 'cost_ci_lower' in cost_data.columns and 'cost_ci_upper' in cost_data.columns else pd.Series([False] * len(cost_data))
        if valid_data.any():
            ax.errorbar(cost_data.loc[valid_data, 'cost_mean'], cost_data.loc[valid_data].index,
                       xerr=[cost_data.loc[valid_data, 'cost_mean'] - cost_data.loc[valid_data, 'cost_ci_lower'],
                             cost_data.loc[valid_data, 'cost_ci_upper'] - cost_data.loc[valid_data, 'cost_mean']],
                       fmt='none', color='black', capsize=3)

        format_axis_currency(ax, axis='x')
        ax.set_xlabel('Cost (A$)')
        ax.set_title('Cost Comparison: Ketamine vs Electroconvulsive Therapy (Lowest Cost = Green)')

        # Cost savings potential - incremental cost analysis
        ax = axes[0, 1]
        cost_data_sorted = cost_data.sort_values('cost_mean').reset_index(drop=True)
        if len(cost_data_sorted) > 1:
            incremental_costs = []
            strategies = []
            base_cost = pd.to_numeric(cost_data_sorted.loc[0, 'cost_mean'], errors='coerce')
            base_cost = 0.0 if pd.isna(base_cost) else base_cost

            for i in range(1, len(cost_data_sorted)):
                this_cost = pd.to_numeric(cost_data_sorted.loc[i, 'cost_mean'], errors='coerce')
                this_cost = 0.0 if pd.isna(this_cost) else this_cost
                inc_cost = this_cost - base_cost
                incremental_costs.append(inc_cost)
                strategies.append(f"{cost_data_sorted.loc[i, 'display_strategy']}\nvs {cost_data_sorted.loc[0, 'display_strategy']}")

            ax.barh(strategies, incremental_costs, color='coral', alpha=0.7)
            format_axis_currency(ax, axis='x')
            ax.set_xlabel('Incremental Cost (A$)')
            ax.set_title('Incremental Cost Analysis: Ketamine vs Electroconvulsive Therapy')

            # Add value labels
            max_inc = max(incremental_costs) if incremental_costs else 0.0
            for i, v in enumerate(incremental_costs):
                offset = max_inc * 0.01 if max_inc > 0 else 0.0
                x_pos = v + offset if v > 0 else v - max_inc * 0.05 if max_inc > 0 else v - 0.01
                ax.text(x_pos, i, f'A${v:,.0f}', va='center', fontsize=10)
        else:
            ax.text(0.5, 0.5, 'Insufficient data for\nincremental analysis', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Incremental Cost Analysis: Ketamine vs Electroconvulsive Therapy')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)

        # Cost distribution analysis - prefer base_case_results boxplots
        ax = axes[1, 0]
        if getattr(results, 'base_case_results', None) is not None and not results.base_case_results.empty:
            strategies_list = []
            cost_values = []
            for strategy in all_strategies:
                if strategy in results.base_case_results['strategy'].values:
                    strategy_costs = results.base_case_results[results.base_case_results['strategy'] == strategy]['cost'].values
                    if len(strategy_costs) > 0:
                        strategies_list.append(display_map.get(strategy, strategy))
                        cost_values.append(strategy_costs)

            if strategies_list and cost_values:
                bp = ax.boxplot(cost_values, labels=strategies_list, patch_artist=True)
                for patch in bp['boxes']:
                    patch.set_facecolor('lightblue')
                    patch.set_alpha(0.7)
                for median in bp['medians']:
                    median.set_color('red')
                    median.set_linewidth(2)
                ax.set_title('Cost Distribution Analysis: Ketamine vs Electroconvulsive Therapy')
                ax.set_xlabel('Treatment Strategy')
                ax.set_ylabel('Cost (A$)')
                format_axis_currency(ax, axis='y')
                plt.xticks(rotation=45, ha='right')
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, 'Insufficient data for\ncost distribution analysis', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Cost Distribution Analysis: Ketamine vs Electroconvulsive Therapy')
        else:
            # Fallback: summary bar with CIs
            if not cost_data.empty:
                summary = cost_data.copy().sort_values('cost_mean')
                y_positions = range(len(summary))
                ax.barh(summary['display_strategy'], summary['cost_mean'], color='lightblue', alpha=0.8)
                if 'cost_ci_lower' in summary.columns and 'cost_ci_upper' in summary.columns:
                    lower_err = summary['cost_mean'] - summary['cost_ci_lower']
                    upper_err = summary['cost_ci_upper'] - summary['cost_mean']
                    ax.errorbar(summary['cost_mean'], y_positions, xerr=[lower_err.values, upper_err.values], fmt='none', color='black', capsize=3)
                ax.set_title('Cost Distribution Summary: Ketamine vs Electroconvulsive Therapy')
                ax.set_xlabel('Cost (A$)')
                format_axis_currency(ax, axis='x')
                plt.tight_layout()
            else:
                ax.text(0.5, 0.5, 'No data available for\ncost distribution analysis', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Cost Distribution Analysis: Ketamine vs Electroconvulsive Therapy')

        # Cost-effectiveness plane for equivalent strategies
        ax = axes[1, 1]
        if getattr(results, 'base_case_results', None) is not None and not results.base_case_results.empty:
            from analysis.plotting.publication import _get_cmap
            cmap = _get_cmap('tab10')
            colors = cmap(np.linspace(0, 1, len(all_strategies)))
            strategy_colors = dict(zip(all_strategies, colors))
            for strategy in all_strategies:
                strategy_data = results.base_case_results[results.base_case_results['strategy'] == strategy]
                if not strategy_data.empty:
                    mean_cost = strategy_data['cost'].mean()
                    mean_effect = strategy_data['effect'].mean()
                    ax.scatter(mean_effect, mean_cost, s=100, alpha=0.7, color=strategy_colors[strategy], label=display_map.get(strategy, strategy))
                    if len(strategy_data) > 1:
                        cost_std = strategy_data['cost'].std()
                        effect_std = strategy_data['effect'].std()
                        ax.errorbar(mean_effect, mean_cost, xerr=effect_std, yerr=cost_std, fmt='none', alpha=0.5, capsize=3, color=strategy_colors[strategy])
            ax.set_title('Cost-Effectiveness Plane: Ketamine vs Electroconvulsive Therapy')
            ax.set_xlabel('Effect (QALYs)')
            ax.set_ylabel('Cost (A$)')
            format_axis_currency(ax, axis='y')
            _handles, _labels = ax.get_legend_handles_labels()
            if _handles:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)
        else:
            # Fallback: plot mean effect vs mean cost from cost_minimization_results
            if not cost_data.empty:
                from analysis.plotting.publication import _get_cmap
                cmap = _get_cmap('tab10')
                colors = cmap(np.linspace(0, 1, len(cost_data)))
                for i, row in cost_data.sort_values('cost_mean').iterrows():
                    mean_cost = row.get('cost_mean', 0.0)
                    mean_effect = row.get('effect_mean', 0.0)
                    ax.scatter(mean_effect, mean_cost, s=100, alpha=0.8, label=row.get('display_strategy'))
                    if 'effect_ci_lower' in row and 'effect_ci_upper' in row and 'cost_ci_lower' in row and 'cost_ci_upper' in row:
                        eff_lo = mean_effect - row['effect_ci_lower'] if pd.notna(row['effect_ci_lower']) else 0
                        eff_hi = row['effect_ci_upper'] - mean_effect if pd.notna(row['effect_ci_upper']) else 0
                        cost_lo = mean_cost - row['cost_ci_lower'] if pd.notna(row['cost_ci_lower']) else 0
                        cost_hi = row['cost_ci_upper'] - mean_cost if pd.notna(row['cost_ci_upper']) else 0
                        ax.errorbar(mean_effect, mean_cost, xerr=[[eff_lo], [eff_hi]], yerr=[[cost_lo], [cost_hi]], fmt='none', alpha=0.5, capsize=3)
                ax.set_title('Cost-Effectiveness Plane Summary: Ketamine vs Electroconvulsive Therapy')
                ax.set_xlabel('Effect (QALYs)')
                ax.set_ylabel('Cost (A$)')
                format_axis_currency(ax, axis='y')
                _handles, _labels = ax.get_legend_handles_labels()
                if _handles:
                    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, 'No data available for\ncost-effectiveness plane', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Cost-Effectiveness Plane: Ketamine vs Electroconvulsive Therapy')

        plt.tight_layout()

        if save_path:
            save_multiformat(fig, Path(save_path))

        return fig


def plot_cma_sensitivity_analysis(
    results: CMAResults,
    save_path: Optional[str] = None,
    include_all_strategies: bool = True,
    **kwargs
) -> Figure:
    """
    Plot CMA sensitivity analysis results.

    Args:
        results: CMA analysis results
        save_path: Path to save figure
        include_all_strategies: If True, ensure all 10 treatment strategies are included
                               in plots even if they lack sensitivity data
        **kwargs: Additional plotting arguments

    Returns:
        Matplotlib figure
    """
    # Data validation assertions
    assert hasattr(results, 'sensitivity_analysis'), "CMAResults object missing 'sensitivity_analysis' attribute"

    # Strategy coverage validation
    from analysis.core.io import StrategyConfig
    from pathlib import Path
    config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
    # Filter out step-care sequences for basic CMA analysis
    expected_strategies = set([s for s in config.strategies if not s.startswith('Step-care:')])
    print(f"CMA sensitivity plot - Expected individual strategies: {expected_strategies}")

    with journal_style():
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        sensitivity_data = results.sensitivity_analysis.copy()

        # Equivalence margin sensitivity
        margin_data = sensitivity_data[sensitivity_data['parameter'] == 'equivalence_margin']

        if not margin_data.empty:
            ax = axes[0]
            ax.plot(margin_data['value'], margin_data['equivalent_pairs'],
                   'o-', linewidth=2, markersize=8, color='blue')

            ax.set_xlabel('Equivalence Margin')
            ax.set_ylabel('Number of Equivalent Pairs')
            ax.set_title('Sensitivity to Equivalence Margin: Ketamine vs Electroconvulsive Therapy')
            ax.grid(True, alpha=0.3)

            # Add reference line at current margin
            current_margin = results.summary_stats.get('equivalence_margin', 0.01)
            if current_margin in margin_data['value'].values:
                current_pairs = margin_data[margin_data['value'] == current_margin]['equivalent_pairs'].iloc[0]
                ax.plot(current_margin, current_pairs, 'ro', markersize=10,
                        label=f'Current margin ({current_margin})')
                _handles, _labels = ax.get_legend_handles_labels()
                if _handles:
                    ax.legend()

        # Cost threshold analysis - show willingness to pay analysis
        ax = axes[1]
        if not results.base_case_results.empty:
            # Get cost and effect data from base case results
            base_data = results.base_case_results.copy()
            cost_data = base_data.groupby('strategy').agg({'cost': ['mean', 'std']}).reset_index()
            cost_data.columns = ['strategy', 'cost_mean', 'cost_std']
            effect_data = base_data.groupby('strategy').agg({'effect': ['mean', 'std']}).reset_index()
            effect_data.columns = ['strategy', 'effect_mean', 'effect_std']
            
            # Merge data
            threshold_data = pd.merge(cost_data, effect_data, on='strategy', how='inner')
            
            if not threshold_data.empty:
                # Calculate ICER for each strategy vs cheapest
                cheapest_cost = threshold_data['cost_mean'].min()
                cheapest_effect = threshold_data[threshold_data['cost_mean'] == cheapest_cost]['effect_mean'].iloc[0]
                
                threshold_data['incremental_cost'] = threshold_data['cost_mean'] - cheapest_cost
                threshold_data['incremental_effect'] = threshold_data['effect_mean'] - cheapest_effect
                threshold_data['icer'] = threshold_data['incremental_cost'] / threshold_data['incremental_effect']
                
                # Remove infinite ICERs and sort
                valid_data = threshold_data[threshold_data['icer'] != float('inf')].copy()
                valid_data = valid_data.sort_values('icer')
                
                if not valid_data.empty:
                    ax.barh(valid_data['strategy'], valid_data['icer'], color='purple', alpha=0.7)
                    ax.axvline(x=50000, color='red', linestyle='--', alpha=0.7, label='$50K threshold')
                    format_axis_currency(ax, axis='x')
                    ax.set_xlabel('ICER ($ per QALY)')
                    ax.set_title('Cost-Effectiveness Thresholds: Ketamine vs Electroconvulsive Therapy')
                    ax.legend()
                    
                    # Add value labels
                    for i, v in enumerate(valid_data['icer']):
                        if pd.notna(v):
                            ax.text(v + max(valid_data['icer']) * 0.01, i, 
                                   f'${v:,.0f}', va='center', fontsize=10)
                else:
                    ax.text(0.5, 0.5, 'Insufficient data for\\nthreshold analysis',
                           ha='center', va='center', transform=ax.transAxes)
                    ax.set_title('Cost-Effectiveness Thresholds: Ketamine vs Electroconvulsive Therapy')
            else:
                ax.text(0.5, 0.5, 'No data available for\\nthreshold analysis',
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Cost-Effectiveness Thresholds: Ketamine vs Electroconvulsive Therapy')
        else:
            ax.text(0.5, 0.5, 'No data available for\\nthreshold analysis',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Cost-Effectiveness Thresholds: Ketamine vs Electroconvulsive Therapy')

        plt.tight_layout()

        if save_path:
            save_multiformat(fig, Path(save_path))

        return fig


def create_cma_report_plots(
    results: CMAResults,
    output_dir: Path,
    prefix: str = "cma",
    include_all_strategies: bool = True
) -> Dict[str, str]:
    """
    Create comprehensive CMA report plots.

    Args:
        results: CMA analysis results
        output_dir: Output directory for plots (Path object)
        prefix: File prefix for plot names
        include_all_strategies: If True, ensure all 10 treatment strategies are included
                               in plots even if they lack data

    Returns:
        Dictionary of plot file paths
    """
    # Data validation assertions
    assert hasattr(results, 'equivalence_tests'), "CMAResults object missing 'equivalence_tests' attribute"
    assert hasattr(results, 'cost_minimization_results'), "CMAResults object missing 'cost_minimization_results' attribute"
    assert hasattr(results, 'sensitivity_analysis'), "CMAResults object missing 'sensitivity_analysis' attribute"

    # Strategy coverage validation
    from analysis.core.io import StrategyConfig
    from pathlib import Path
    config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
    # Filter out step-care sequences for basic CMA analysis
    expected_strategies = set([s for s in config.strategies if not s.startswith('Step-care:')])
    print(f"CMA report generation - Expected individual strategies: {expected_strategies}")

    output_dir.mkdir(parents=True, exist_ok=True)

    plot_files = {}

    # Equivalence tests plot
    fig1 = plot_cma_equivalence_tests(results, include_all_strategies=include_all_strategies)
    path1 = output_dir / f"{prefix}_equivalence_tests"
    save_multiformat(fig1, path1)
    plt.close(fig1)
    plot_files['equivalence_tests'] = str(path1)

    # Cost comparison plot
    fig2 = plot_cma_cost_comparison(results, include_all_strategies=include_all_strategies)
    path2 = output_dir / f"{prefix}_cost_comparison"
    save_multiformat(fig2, path2)
    plt.close(fig2)
    plot_files['cost_comparison'] = str(path2)

    # Sensitivity analysis plot
    fig3 = plot_cma_sensitivity_analysis(results, include_all_strategies=include_all_strategies)
    path3 = output_dir / f"{prefix}_sensitivity"
    save_multiformat(fig3, path3)
    plt.close(fig3)
    plot_files['sensitivity'] = str(path3)

    return plot_files
