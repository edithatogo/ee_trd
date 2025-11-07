"""Multi-Criteria Decision Analysis (MCDA) plotting helpers.

This module provides visualization functions for multi-criteria decision analysis
results, including rankings, weighted scores, criteria scores, and sensitivity analysis.
Functions here produce publication-quality figures used in the MCDA reporting pipeline.

Author: V4 Development Team
Date: October 2025
"""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from analysis.plotting.publication import _get_cmap
from matplotlib.figure import Figure
import matplotlib.cm as cm
import seaborn as sns
import pandas as pd
import numpy as np
from scipy import stats
from typing import Optional, Dict, Any, List
from pathlib import Path

from analysis.plotting.publication import (
    journal_style, save_multiformat, format_axis_currency,
    format_axis_percentage, add_reference_line
)


def plot_mcda_rankings(rankings_df, output_path):
    """Plot MCDA strategy rankings.

    Args:
        rankings_df: DataFrame with columns ['strategy', 'rank', 'score']
        output_path: Path to save the figure
    """
    with journal_style():
        fig, ax = plt.subplots(figsize=(10, 6))

        # Sort by rank
        rankings_df = rankings_df.sort_values('rank')

        # Create horizontal bar chart
        _bars = ax.barh(rankings_df['strategy'], rankings_df['score'],
                      color=sns.color_palette("viridis", len(rankings_df)))

        # Add rank numbers
        for i, (idx, row) in enumerate(rankings_df.iterrows()):
            ax.text(row['score'] + 0.01, i, f'#{int(row["rank"])}',
                   va='center', fontsize=10, fontweight='bold')

        ax.set_xlabel('MCDA Score')
        ax.set_ylabel('Strategy')
        ax.set_title('MCDA Strategy Rankings')

        # Format x-axis as percentage if scores are normalized
        if rankings_df['score'].max() <= 1.0:
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))

        plt.tight_layout()
        save_multiformat(fig, output_path)
        plt.close(fig)


def plot_mcda_weighted_scores(scores_df, output_path):
    """Plot MCDA weighted scores by strategy and criterion.

    Args:
        scores_df: DataFrame with columns ['strategy', 'criterion', 'weighted_score']
        output_path: Path to save the figure
    """
    with journal_style():
        fig, ax = plt.subplots(figsize=(12, 8))

        # Pivot data for heatmap
        pivot_df = scores_df.pivot(index='strategy', columns='criterion', values='weighted_score')

        # Create heatmap
        sns.heatmap(pivot_df, annot=True, fmt='.3f', cmap='viridis',
                   cbar_kws={'label': 'Weighted Score'}, ax=ax)

        ax.set_title('MCDA Weighted Scores by Strategy and Criterion')
        ax.set_xlabel('Criterion')
        ax.set_ylabel('Strategy')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        save_multiformat(fig, output_path)
        plt.close(fig)


def plot_mcda_criteria_scores(scores_df, output_path):
    """Plot MCDA criteria scores distribution.

    Args:
        scores_df: DataFrame with columns ['strategy', 'criterion', 'score', 'weight']
        output_path: Path to save the figure
    """
    with journal_style():
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Box plot of scores by criterion
        sns.boxplot(data=scores_df, x='criterion', y='score', ax=ax1)
        ax1.set_title('Criteria Scores Distribution')
        ax1.set_xlabel('Criterion')
        ax1.set_ylabel('Score')
        ax1.tick_params(axis='x', rotation=45)

        # Scatter plot of score vs weight
        _scatter = ax2.scatter(scores_df['weight'], scores_df['score'],
                            c=scores_df['strategy'].astype('category').cat.codes,
                            cmap='tab10', alpha=0.7)
        ax2.set_xlabel('Weight')
        ax2.set_ylabel('Score')
        ax2.set_title('Score vs Weight by Strategy')

        # Add legend
        unique_strategies = scores_df['strategy'].unique()
        legend_elements = [Line2D([0], [0], marker='o', color='w',
                        markerfacecolor=_get_cmap('tab10')(i/len(unique_strategies)),
                        markersize=8, label=strategy)
                   for i, strategy in enumerate(unique_strategies)]
        ax2.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()
        save_multiformat(fig, output_path)
        plt.close(fig)


def plot_mcda_sensitivity_analysis(sensitivity_df, output_path):
    """Plot MCDA sensitivity analysis showing rank changes with weight variations.

    Args:
        sensitivity_df: DataFrame with columns ['strategy', 'weight_scenario', 'rank', 'rank_change']
        output_path: Path to save the figure
    """
    with journal_style():
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Rank stability plot
        rank_stability = sensitivity_df.groupby('strategy')['rank'].std().sort_values()
        rank_stability.plot(kind='barh', ax=ax1, color='skyblue')
        ax1.set_xlabel('Rank Standard Deviation')
        ax1.set_title('MCDA Rank Stability Across Weight Scenarios')
        ax1.grid(True, alpha=0.3)

        # Rank change distribution
        if 'rank_change' in sensitivity_df.columns:
            sensitivity_df['rank_change'].hist(ax=ax2, bins=10, alpha=0.7)
            ax2.set_xlabel('Rank Change')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Distribution of Rank Changes')
            ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='No Change')
            ax2.legend()
        else:
            # Alternative: show rank distribution by scenario
            sns.boxplot(data=sensitivity_df, x='weight_scenario', y='rank', ax=ax2)
            ax2.set_xlabel('Weight Scenario')
            ax2.set_ylabel('Rank')
            ax2.set_title('Rank Distribution by Weight Scenario')
            ax2.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        save_multiformat(fig, output_path)
        plt.close(fig)
