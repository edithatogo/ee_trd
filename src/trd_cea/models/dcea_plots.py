"""
Distributional Cost-Effectiveness Analysis Plotting

Publication-quality plots for DCEA and equity analysis.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import unicodedata

from trd_cea.core.log_utils import create_analysis_logger

# Create logger
logger = create_analysis_logger(__name__)


def normalize_label_for_matching(s: str) -> str:
    """Public normalization helper for subgroup label matching.

    Normalizes unicode diacritics, lowercases and converts non-alphanumerics
    to underscores. Used by plotting and tests.
    """
    if s is None:
        return ''
    s = str(s)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^0-9a-z]+", '_', s)
    s = s.strip('_')
    return s

from analysis.plotting.publication import (  # noqa: E402
    figure_context, save_multiformat, add_reference_line,
    format_axis_percentage, create_legend, format_axis_wtp, JournalStandards
)

__all__ = [
    "plot_equity_impact_plane",
    "plot_atkinson_index",
    "plot_ede_qalys",
    "plot_distributional_ceac",
    "plot_subgroup_comparison",
    "plot_age_subgroup_analysis",
    "plot_gender_subgroup_analysis",
    "plot_severity_subgroup_analysis",
    "plot_indigenous_subgroup_analysis",
    "plot_comprehensive_dcea_forest_plot",
]


def plot_equity_impact_plane(
    total_qalys: pd.DataFrame,
    inequality: pd.DataFrame,
    output_path: Path,
    reference_strategy: str,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create equity impact plane showing total QALYs vs inequality.
    
    Args:
        total_qalys: DataFrame with strategies as columns
        inequality: DataFrame with strategies as columns (Atkinson index)
        output_path: Output file path
        reference_strategy: Reference strategy name
        title: Optional custom title
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Equity Impact Plane:\nHealth Outcomes vs Inequality in Ketamine vs ECT Therapies"
    
    # Calculate incremental values
    inc_qalys = total_qalys.subtract(total_qalys[reference_strategy], axis=0)
    inc_inequality = inequality.subtract(inequality[reference_strategy], axis=0)
    
    with figure_context(
        title=title,
        xlabel="Incremental Total Quality-Adjusted Life Years (QALYs)",
        ylabel="Incremental Inequality\n(Atkinson Index, ε=1.5)",
        standards=standards
    ) as (fig, ax):
        
        # Plot each strategy
        for strategy in inc_qalys.columns:
            if strategy == reference_strategy:
                continue
            
            ax.scatter(
                inc_qalys[strategy],
                inc_inequality[strategy],
                alpha=0.8,
                s=20,
                label=strategy
            )
        
        # Add reference lines
        add_reference_line(ax, 0, 'horizontal', color='gray', alpha=0.5)
        add_reference_line(ax, 0, 'vertical', color='gray', alpha=0.5)
        
        # Add quadrant labels
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        ax.text(xlim[1]*0.7, ylim[1]*0.7, 'More QALYs\nMore Inequality',
                ha='center', va='center', fontsize=8, alpha=0.5)
        ax.text(xlim[1]*0.7, ylim[0]*0.7, 'More QALYs\nLess Inequality',
                ha='center', va='center', fontsize=8, alpha=0.5)
        
        # Add legend
        create_legend(ax, location='upper left')
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_atkinson_index(
    atkinson_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create Atkinson inequality index comparison plot.
    
    Args:
        atkinson_data: DataFrame with strategies and Atkinson values
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Atkinson Inequality Index Comparison:\nHealth Inequality Across Ketamine vs ECT Treatment Strategies"
    
    with figure_context(
        title=title,
        xlabel="Treatment Strategy",
        ylabel="Atkinson Inequality Index\n(ε=1.5, higher values = more inequality)",
        figsize=(8, 5),
        standards=standards
    ) as (fig, ax):
        
        # Create bar plot
        strategies = atkinson_data['strategy'].values
        values = atkinson_data['atkinson'].values
        
        bars = ax.bar(range(len(strategies)), values, alpha=0.7, color='steelblue')
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.3f}',
                   ha='center', va='bottom', fontsize=8)
        
        # Set x-axis labels
        ax.set_xticks(range(len(strategies)))
        ax.set_xticklabels(strategies, rotation=45, ha='right')
        
        # Add reference line at 0
        add_reference_line(ax, 0, 'horizontal', color='gray', alpha=0.5)
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_ede_qalys(
    ede_data: pd.DataFrame,
    total_qalys: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create EDE-QALYs comparison plot.
    
    Args:
        ede_data: DataFrame with strategies and EDE-QALY values
        total_qalys: DataFrame with strategies and total QALY values
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Equally Distributed Equivalent Quality-Adjusted Life Years:\nEquity-Weighted Outcomes for Ketamine vs ECT Therapies"
    
    with figure_context(
        title=title,
        xlabel="Treatment Strategy",
        ylabel="Equally Distributed Equivalent\nQuality-Adjusted Life Years (QALYs)",
        figsize=(8, 5),
        standards=standards
    ) as (fig, ax):
        
        strategies = ede_data['strategy'].values
        x = np.arange(len(strategies))
        width = 0.35
        
        # Plot total QALYs and EDE-QALYs
        ax.bar(x - width/2, total_qalys['total_qalys'].values,
               width, label='Total QALYs', alpha=0.7)
        ax.bar(x + width/2, ede_data['ede_qalys'].values,
               width, label='EDE-QALYs', alpha=0.7)
        
        # Set x-axis labels
        ax.set_xticks(x)
        ax.set_xticklabels(strategies, rotation=45, ha='right')
        
        # Add legend
        create_legend(ax, location='best')
        
        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)
    
    return artifacts.base_path


def plot_distributional_ceac(
    dceac_data: pd.DataFrame,
    output_path: Path,
    epsilon: float = 1.0,
    title: Optional[str] = None,
    currency: str = 'A$',
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create distributional cost-effectiveness acceptability curve.
    
    Args:
        dceac_data: DataFrame with WTP thresholds and probabilities
        output_path: Output file path
        epsilon: Inequality aversion parameter
        title: Optional custom title
        currency: Currency symbol
        standards: Journal standards
    
    Returns:
        Path to saved figure
    """
    if title is None:
        title = f"Distributional CEAC (ε = {epsilon})"
    
    with figure_context(
        title=title,
        xlabel=f"Willingness-to-Pay Threshold ({currency}/QALY)",
        ylabel="Probability Cost-Effective",
        standards=standards
    ) as (fig, ax):
        
        # Plot each strategy
        for strategy in dceac_data.columns:
            if strategy == 'wtp':
                continue
            ax.plot(
                dceac_data['wtp'],
                dceac_data[strategy],
                label=strategy,
                linewidth=2
            )
        # Format axes: WTP axis should use currency label and thousands separator
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


def plot_subgroup_comparison(
    subgroup_data: pd.DataFrame,
    output_path: Path,
    metric: str = 'ICER',
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create subgroup comparison plot.

    Args:
        subgroup_data: DataFrame with subgroups, strategies, and metric values
        output_path: Output file path
        metric: Metric name for y-axis
        title: Optional custom title
        standards: Journal standards

    Returns:
        Path to saved figure
    """
    if title is None:
        title = f"{metric} by Subgroup"

    # The data comes as: strategy, subgroup, effect, cost, icer
    # We need to pivot it to: subgroup as index, strategy as columns, metric as values

    try:
        # Pivot data for plotting
        pivot_data = subgroup_data.pivot(
            index='subgroup',
            columns='strategy',
            values=metric.lower()
        )

        with figure_context(
            title=title,
            xlabel="Subgroup",
            ylabel=metric,
            figsize=(10, 6),
            standards=standards
        ) as (fig, ax):

            # Create grouped bar plot
            pivot_data.plot(kind='bar', ax=ax, alpha=0.7, width=0.8)

            # Rotate x-axis labels
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

            # Add legend
            create_legend(ax, location='best')

            # Save figure
            artifacts = save_multiformat(fig, output_path, standards=standards)
            plt.close(fig)

        return artifacts.base_path

    except KeyError as e:
        logger.warning(f"Could not create subgroup plot due to missing data structure: {e}")
        logger.debug(f"Available columns: {list(subgroup_data.columns)}")
        logger.debug(f"Available subgroups: {subgroup_data['subgroup'].unique()}")
        logger.debug(f"Available strategies: {subgroup_data['strategy'].unique()}")
        # Return a dummy path since we can't create the plot
        return output_path


def plot_age_subgroup_analysis(
    subgroup_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create age-specific subgroup analysis plot with DCEA focus.

    Args:
        subgroup_data: DataFrame with age subgroups and outcomes
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards

    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Age-Stratified Cost-Effectiveness Analysis:\nICER by Age Group with Equity Considerations"

    # Filter to age subgroups only
    age_subgroups = ['young_adults', 'middle_aged', 'older_adults']
    age_data = subgroup_data[subgroup_data['subgroup'].isin(age_subgroups)].copy()

    if age_data.empty:
        logger.warning("No age subgroup data found")
        return output_path

    try:
        # Pivot for age-specific plotting
        pivot_data = age_data.pivot(
            index='subgroup',
            columns='strategy',
            values='icer'
        )

        # Sort age groups in logical order
        age_order = ['young_adults', 'middle_aged', 'older_adults']
        pivot_data = pivot_data.reindex(age_order)

        with figure_context(
            title=title,
            xlabel="Age Group",
            ylabel="Incremental Cost-Effectiveness Ratio (ICER)",
            figsize=(10, 6),
            standards=standards
        ) as (fig, ax):

            # Create grouped bar plot
            pivot_data.plot(kind='bar', ax=ax, alpha=0.7, width=0.8)

            # Customize x-axis labels
            ax.set_xticklabels(['Young Adults\n(18-44)', 'Middle-Aged\n(45-64)', 'Older Adults\n(65-100)'],
                             rotation=0, ha='center')

            # Add value labels on bars
            for container in ax.containers:
                ax.bar_label(container, fmt='%.0f', label_type='edge', fontsize=8)

            # Add reference line at common WTP threshold
            add_reference_line(ax, 50000, 'horizontal', label='WTP = A$50,000/QALY')

            # Add legend
            create_legend(ax, location='best')

            # Save figure
            artifacts = save_multiformat(fig, output_path, standards=standards)
            plt.close(fig)

        return artifacts.base_path

    except KeyError as e:
        logger.warning(f"Could not create age subgroup plot: {e}")
        return output_path


def plot_gender_subgroup_analysis(
    subgroup_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create gender-specific subgroup analysis plot.

    Args:
        subgroup_data: DataFrame with gender subgroups and outcomes
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards

    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Gender-Stratified Cost-Effectiveness Analysis:\nICER by Gender with Equity Considerations"

    # Filter to gender subgroups only (excluding age and severity)
    gender_data = subgroup_data[~subgroup_data['subgroup'].isin(
        ['young_adults', 'middle_aged', 'older_adults', 'severe_depression', 'moderate_depression']
    )].copy()

    if gender_data.empty:
        logger.warning("No gender subgroup data found")
        return output_path

    try:
        # Pivot for gender-specific plotting
        pivot_data = gender_data.pivot(
            index='subgroup',
            columns='strategy',
            values='icer'
        )

        with figure_context(
            title=title,
            xlabel="Gender",
            ylabel="Incremental Cost-Effectiveness Ratio (ICER)",
            figsize=(8, 5),
            standards=standards
        ) as (fig, ax):

            # Create grouped bar plot
            pivot_data.plot(kind='bar', ax=ax, alpha=0.7, width=0.8)

            # Customize x-axis labels
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha='center')

            # Add value labels on bars
            for container in ax.containers:
                ax.bar_label(container, fmt='%.0f', label_type='edge', fontsize=8)

            # Add reference line
            add_reference_line(ax, 50000, 'horizontal', label='WTP = A$50,000/QALY')

            # Add legend
            create_legend(ax, location='best')

            # Save figure
            artifacts = save_multiformat(fig, output_path, standards=standards)
            plt.close(fig)

        return artifacts.base_path

    except KeyError as e:
        logger.warning(f"Could not create gender subgroup plot: {e}")
        return output_path


def plot_severity_subgroup_analysis(
    subgroup_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create severity-specific subgroup analysis plot.

    Args:
        subgroup_data: DataFrame with severity subgroups and outcomes
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards

    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Severity-Stratified Cost-Effectiveness Analysis:\nICER by Depression Severity with Equity Considerations"

    # Filter to severity subgroups only
    severity_subgroups = ['severe_depression', 'moderate_depression']
    severity_data = subgroup_data[subgroup_data['subgroup'].isin(severity_subgroups)].copy()

    if severity_data.empty:
        logger.warning("No severity subgroup data found")
        return output_path

    try:
        # Pivot for severity-specific plotting
        pivot_data = severity_data.pivot(
            index='subgroup',
            columns='strategy',
            values='icer'
        )

        # Sort by severity
        severity_order = ['moderate_depression', 'severe_depression']
        pivot_data = pivot_data.reindex(severity_order)

        with figure_context(
            title=title,
            xlabel="Depression Severity",
            ylabel="Incremental Cost-Effectiveness Ratio (ICER)",
            figsize=(10, 6),
            standards=standards
        ) as (fig, ax):

            # Create grouped bar plot
            pivot_data.plot(kind='bar', ax=ax, alpha=0.7, width=0.8)

            # Customize x-axis labels
            ax.set_xticklabels(['Moderate\nDepression', 'Severe\nDepression'],
                             rotation=0, ha='center')

            # Add value labels on bars
            for container in ax.containers:
                ax.bar_label(container, fmt='%.0f', label_type='edge', fontsize=8)

            # Add reference line
            add_reference_line(ax, 50000, 'horizontal', label='WTP = A$50,000/QALY')

            # Add legend
            create_legend(ax, location='best')

            # Save figure
            artifacts = save_multiformat(fig, output_path, standards=standards)
            plt.close(fig)

        return artifacts.base_path

    except KeyError as e:
        logger.warning(f"Could not create severity subgroup plot: {e}")
        return output_path


def plot_indigenous_subgroup_analysis(
    subgroup_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create Indigenous population-specific subgroup analysis plot.

    Args:
        subgroup_data: DataFrame with Indigenous subgroups and outcomes
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards

    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Indigenous Population Cost-Effectiveness Analysis:\nICER by Population Group with Cultural Equity Considerations"

    # Look for Indigenous population data (may not be in current dataset)
    indigenous_indicators = ['indigenous', 'aboriginal', 'maori', 'pacifica', 'first_nations']
    indigenous_data = subgroup_data[subgroup_data['subgroup'].str.contains(
        '|'.join(indigenous_indicators), case=False, na=False
    )].copy()

    if indigenous_data.empty:
        logger.warning("No Indigenous subgroup data found in current dataset")
        logger.debug(f"Available subgroups: {subgroup_data['subgroup'].unique()}")
        return output_path

    try:
        # Pivot for Indigenous-specific plotting
        pivot_data = indigenous_data.pivot(
            index='subgroup',
            columns='strategy',
            values='icer'
        )

        with figure_context(
            title=title,
            xlabel="Population Group",
            ylabel="Incremental Cost-Effectiveness Ratio (ICER)",
            figsize=(10, 6),
            standards=standards
        ) as (fig, ax):

            # Create grouped bar plot
            pivot_data.plot(kind='bar', ax=ax, alpha=0.7, width=0.8)

            # Customize x-axis labels
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha='center')

            # Add value labels on bars
            for container in ax.containers:
                ax.bar_label(container, fmt='%.0f', label_type='edge', fontsize=8)

            # Add reference line
            add_reference_line(ax, 50000, 'horizontal', label='WTP = A$50,000/QALY')

            # Add legend
            create_legend(ax, location='best')

            # Save figure
            artifacts = save_multiformat(fig, output_path, standards=standards)
            plt.close(fig)

        return artifacts.base_path

    except KeyError as e:
        logger.warning(f"Could not create Indigenous subgroup plot: {e}")
        return output_path


def plot_comprehensive_dcea_forest_plot(
    subgroup_data: pd.DataFrame,
    output_path: Path,
    title: Optional[str] = None,
    standards: Optional[JournalStandards] = None,
) -> Path:
    """
    Create a comprehensive forest plot showing all DCEA subgroups in a single visualization.

    This plot combines age, gender, severity, and indigenous subgroups into one unified
    forest plot format commonly used in health economics for subgroup analysis.

    Args:
        subgroup_data: DataFrame with all subgroup data
        output_path: Output file path
        title: Optional custom title
        standards: Journal standards

    Returns:
        Path to saved figure
    """
    if title is None:
        title = "Comprehensive Distributional Cost-Effectiveness Analysis:\nSubgroup Analysis Forest Plot - Ketamine vs ECT Therapies"

    try:
        # The data is already in the correct format: each row has strategy, subgroup, and icer
        # We can use it directly without additional grouping

        # Organize subgroups by category for plotting (use normalized matching)
        age_subgroups = ['young_adults', 'middle_aged', 'older_adults']
        gender_subgroups = ['male', 'female', 'other']
        severity_subgroups = ['severe_depression', 'moderate_depression']
        indigenous_subgroups = ['non_indigenous', 'aboriginal', 'maori', 'pacific_islander']

        # Normalization helper to make matching robust to case, punctuation,
        # underscores/spaces/dashes and common diacritics (e.g. Māori)
        def _normalize_label(s: str) -> str:
            if s is None:
                return ''
            # Normalize unicode (decompose diacritics), lower-case
            s = str(s)
            s = unicodedata.normalize('NFKD', s)
            # Remove diacritic marks
            s = ''.join(ch for ch in s if not unicodedata.combining(ch))
            s = s.lower()
            # Replace non-alphanumeric with underscore
            s = re.sub(r"[^0-9a-z]+", '_', s)
            s = s.strip('_')
            return s

        # Create a normalized copy of subgroup names for robust matching
        subgroup_norm = subgroup_data['subgroup'].astype(str).apply(_normalize_label)

        # Create plot with multiple panels
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(title, fontsize=14, fontweight='bold')

        # Flatten axes for easier iteration
        axes = axes.flatten()

        # Color scheme for different strategies
        import matplotlib.colors as mcolors
        strategies = subgroup_data['strategy'].unique()
        strategy_colors = list(mcolors.TABLEAU_COLORS.values())[:len(strategies)]
        strategy_color_map = dict(zip(strategies, strategy_colors))

        # Plot 1: Age subgroups
        ax1 = axes[0]
        wtp_threshold = 50000

        # Select rows by normalized subgroup labels so variants match robustly
        norm_age_keys = [_normalize_label(s) for s in age_subgroups]
        age_mask = subgroup_norm.isin(norm_age_keys)
        age_data = subgroup_data[age_mask]
        if not age_data.empty:
            _plot_forest_panel_simple(
                ax1,
                age_data,
                'Age Groups',
                strategy_color_map,
                subgroup_order=age_subgroups,
                wtp_threshold=wtp_threshold,
            )
            ax1.set_title('Age-Stratified Analysis')
        else:
            logger.info(f'Age panel empty after normalization. Available subgroups: {subgroup_data["subgroup"].unique()}')
            ax1.set_title('Age-Stratified Analysis (No data)')
            ax1.text(0.5, 0.5, 'No age subgroup data available', ha='center', va='center', transform=ax1.transAxes)

        # Plot 2: Gender subgroups
        ax2 = axes[1]
        norm_gender_keys = [_normalize_label(s) for s in gender_subgroups]
        gender_mask = subgroup_norm.isin(norm_gender_keys)
        gender_data = subgroup_data[gender_mask]
        if not gender_data.empty:
            _plot_forest_panel_simple(
                ax2,
                gender_data,
                'Gender',
                strategy_color_map,
                subgroup_order=gender_subgroups,
                wtp_threshold=wtp_threshold,
            )
            ax2.set_title('Gender-Stratified Analysis')
        else:
            logger.info(f'Gender panel empty after normalization. Available subgroups: {subgroup_data["subgroup"].unique()}')
            ax2.set_title('Gender-Stratified Analysis (No data)')
            ax2.text(0.5, 0.5, 'No gender subgroup data available', ha='center', va='center', transform=ax2.transAxes)

        # Plot 3: Severity subgroups
        ax3 = axes[2]
        norm_severity_keys = [_normalize_label(s) for s in severity_subgroups]
        severity_mask = subgroup_norm.isin(norm_severity_keys)
        severity_data = subgroup_data[severity_mask]
        if not severity_data.empty:
            _plot_forest_panel_simple(
                ax3,
                severity_data,
                'Depression Severity',
                strategy_color_map,
                subgroup_order=severity_subgroups,
                wtp_threshold=wtp_threshold,
            )
            ax3.set_title('Severity-Stratified Analysis')
        else:
            logger.info(f'Severity panel empty after normalization. Available subgroups: {subgroup_data["subgroup"].unique()}')
            ax3.set_title('Severity-Stratified Analysis (No data)')
            ax3.text(0.5, 0.5, 'No severity subgroup data available', ha='center', va='center', transform=ax3.transAxes)

        # Plot 4: Indigenous subgroups
        ax4 = axes[3]
        norm_indigenous_keys = [_normalize_label(s) for s in indigenous_subgroups]
        indigenous_mask = subgroup_norm.isin(norm_indigenous_keys)
        indigenous_data = subgroup_data[indigenous_mask]
        if not indigenous_data.empty:
            _plot_forest_panel_simple(
                ax4,
                indigenous_data,
                'Population Group',
                strategy_color_map,
                subgroup_order=indigenous_subgroups,
                wtp_threshold=wtp_threshold,
            )
            ax4.set_title('Indigenous Population Analysis')
        else:
            logger.info(f'Indigenous panel empty after normalization. Available subgroups: {subgroup_data["subgroup"].unique()}')
            ax4.set_title('Indigenous Population Analysis (No data)')
            ax4.text(0.5, 0.5, 'No Indigenous subgroup data available', ha='center', va='center', transform=ax4.transAxes)

        # Add overall title and WTP reference
        fig.text(0.5, 0.05, 'Incremental Cost-Effectiveness Ratio (ICER) - Point Estimates',
                ha='center', fontsize=12, fontweight='bold')
        fig.tight_layout(rect=(0, 0.06, 1, 1))

        # Save figure
        artifacts = save_multiformat(fig, output_path, standards=standards)
        plt.close(fig)

        return artifacts.base_path

    except Exception as e:
        logger.warning(f"Could not create comprehensive DCEA forest plot: {e}")
        return output_path


def _plot_forest_panel_simple(
    ax,
    data,
    xlabel,
    strategy_color_map,
    subgroup_order: Optional[List[str]] = None,
    wtp_threshold: Optional[float] = None,
) -> None:
    """
    Helper function to plot a single panel of the forest plot with simple structure.

    Args:
        ax: Matplotlib axes
        data: DataFrame with strategy, subgroup, and icer columns
        xlabel: X-axis label
        strategy_color_map: Color mapping for strategies
    """
    if data.empty:
        ax.set_visible(False)
        return

    def _format_subgroup_label(name: str) -> str:
        if '_' in name:
            return name.replace('_', ' ').title()
        return name

    # Determine plotting order for subgroups (preserve requested order if provided)
    unique_subgroups = list(dict.fromkeys(data['subgroup']))
    if subgroup_order:
        ordered = [sg for sg in subgroup_order if sg in unique_subgroups]
        remaining = [sg for sg in unique_subgroups if sg not in ordered]
        subgroups = ordered + remaining
    else:
        subgroups = unique_subgroups

    yaxis_transform = ax.get_yaxis_transform()

    y_pos = 0.0
    gap = 0.6
    last_subgroup_index = len(subgroups) - 1

    for idx, subgroup in enumerate(subgroups):
        subgroup_data = data[data['subgroup'] == subgroup]
        if subgroup_data.empty:
            continue

        subgroup_data = subgroup_data.copy()
        subgroup_data = subgroup_data.sort_values('strategy')

        subgroup_height = len(subgroup_data)
        subgroup_center = y_pos + (subgroup_height - 1) / 2.0 if subgroup_height else y_pos

        # Add subgroup label along the left margin (axes coordinates for x, data for y)
        ax.text(
            -0.03,
            subgroup_center,
            _format_subgroup_label(subgroup),
            ha='right',
            va='center',
            fontsize=9,
            fontweight='bold',
            transform=yaxis_transform,
        )

        for _, row in subgroup_data.iterrows():
            icer_value = row['icer']
            strategy = row['strategy']
            color = strategy_color_map.get(strategy, 'tab:blue')
            row_y = y_pos

            # Plot horizontal line (representing the estimate)
            ax.hlines(
                row_y,
                xmin=min(0, icer_value),
                xmax=icer_value,
                colors=color,
                linewidth=2,
                alpha=0.8,
            )

            # Plot the ICER point
            ax.plot(
                icer_value,
                row_y,
                'o',
                color=color,
                markersize=6,
            )

            # Add strategy label on the left
            ax.text(
                -0.18,
                row_y,
                f"{strategy}",
                ha='right',
                va='center',
                fontsize=7,
                transform=yaxis_transform,
            )

            # Add ICER value label
            ax.text(
                icer_value + 1000,
                row_y,
                f"{icer_value:,.0f}",
                ha='left',
                va='center',
                fontsize=7,
            )

            y_pos += 1

        # Add subgroup separator line and vertical spacing (except after the last subgroup)
        if idx < last_subgroup_index:
            if len(subgroup_data) > 0:
                ax.axhline(y=y_pos - 0.5, color='lightgray', linewidth=0.5, linestyle='--', alpha=0.6)
            y_pos += gap

    # Configure axes appearance
    if y_pos == 0:
        max_y = 0.5
    else:
        max_y = y_pos - 0.5

    ax.set_ylim(-0.5, max_y)
    ax.invert_yaxis()
    ax.set_yticks([])
    ax.set_ylabel('')
    ax.set_xlabel(f'Incremental Cost-Effectiveness Ratio (ICER) - {xlabel}')
    ax.grid(True, alpha=0.3, axis='x', linestyle=':')

    # Determine sensible x-axis limits
    icer_values = data['icer'].dropna()
    if not icer_values.empty:
        min_icer = min(0.0, float(icer_values.min()))
        max_icer = float(icer_values.max())
    else:
        min_icer, max_icer = 0.0, 1.0

    if wtp_threshold is not None:
        max_icer = max(max_icer, float(wtp_threshold))

    x_padding = max(1000.0, 0.05 * (max_icer - min_icer if max_icer != min_icer else max_icer or 1.0))
    ax.set_xlim(min_icer - x_padding, max_icer + x_padding)

    if wtp_threshold is not None:
        ax.axvline(
            x=wtp_threshold,
            color='red',
            linestyle='--',
            alpha=0.7,
            linewidth=2,
        )
        ylim = ax.get_ylim()
        ax.annotate(
            'WTP\nThreshold',
            xy=(wtp_threshold, ylim[0]),
            xycoords=('data', 'data'),
            xytext=(0, -20),
            textcoords='offset points',
            ha='center',
            va='top',
            fontsize=8,
            color='red',
            fontweight='bold',
        )


def _plot_forest_panel(ax, data, xlabel, strategy_colors):
    """
    Helper function to plot a single panel of the forest plot.

    Args:
        ax: Matplotlib axes
        data: DataFrame with summary statistics
        xlabel: X-axis label
        strategy_colors: Color scheme for strategies
    """
    strategy_color_map = dict(zip(data['strategy'].unique(), strategy_colors))

    y_pos = 0
    subgroups = sorted(data['subgroup'].unique())

    for subgroup in subgroups:
        subgroup_data = data[data['subgroup'] == subgroup]

        # Add subgroup label
        ax.text(-0.05, y_pos + len(subgroup_data)/2, f"{subgroup}",
               ha='right', va='center', fontsize=9, fontweight='bold',
               transform=ax.transAxes)

        for _, row in subgroup_data.iterrows():
            # For this data structure, we don't have confidence intervals
            # So we'll plot just the point estimate with a line
            icer_value = row['icer']

            # Plot horizontal line (representing the estimate)
            ax.plot([0, icer_value], [y_pos, y_pos],
                   color=strategy_color_map[row['strategy']], linewidth=2, alpha=0.8)

            # Plot the ICER point
            ax.plot(icer_value, y_pos, 'o',
                   color=strategy_color_map[row['strategy']], markersize=5)

            # Add strategy label on the left
            ax.text(-0.15, y_pos, f"{row['strategy']}",
                   ha='right', va='center', fontsize=7,
                   transform=ax.transAxes)

            # Add ICER value label
            ax.text(icer_value + 1000, y_pos, f"{icer_value:.0f}",
                   ha='left', va='center', fontsize=7)

            y_pos += 1

        # Add subgroup separator
        y_pos += 0.8

    ax.set_xlabel(f'Incremental Cost-Effectiveness Ratio (ICER) - {xlabel}')
    ax.set_ylabel('Treatment Strategy by Subgroup')
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(0, 80000)  # Set reasonable x-axis limits
