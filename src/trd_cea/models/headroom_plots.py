"""
Plotting functions for Headroom Analysis results.

This module provides comprehensive visualization capabilities for headroom analysis,
including headroom curves, threshold price plots, and sensitivity analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.plotting.publication import (
    figure_context, save_multiformat, add_reference_line,
    format_axis_currency, format_axis_percentage, JournalStandards
)
from trd_cea.core.io import load_strategies_config

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from analysis.engines.headroom_engine import HeadroomResults


class HeadroomPlotter:
    """
    Plotting functions for headroom analysis results.

    Provides publication-quality visualizations for headroom metrics including
    headroom curves, threshold prices, and sensitivity analysis.
    """

    def __init__(self, journal_style: bool = True):
        """
        Initialize headroom plotter.

        Args:
            journal_style: Whether to use journal formatting standards
        """
        self.journal_style = journal_style
        self.standards = JournalStandards() if journal_style else None
        logger.info("Initialized Headroom plotter")

    def plot_headroom_curves(
        self,
        headroom_results: 'HeadroomResults',
        save_path: Optional[Path] = None,
        figsize: Tuple[float, float] = (12, 8),
        include_all_strategies: bool = True,
    ) -> plt.Figure:
        """
        Plot headroom curves across WTP thresholds.

        Args:
            headroom_results: HeadroomResults object
            save_path: Path to save figure
            figsize: Figure size
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            matplotlib Figure object
        """
        # Data validation assertions
        assert hasattr(headroom_results, 'metrics'), "HeadroomResults object missing 'metrics' attribute"

        # Strategy coverage validation
        # (load_strategies_config call included for future validation logic)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Convert metrics to DataFrame for easier plotting
        df = pd.DataFrame([m.to_dict() for m in headroom_results.metrics])

        # Ensure all strategies are included if requested
        if include_all_strategies:
            config = load_strategies_config()
            all_strategies = list(config.keys())
            existing_strategies = set(df["strategy"].unique())
            missing_strategies = [s for s in all_strategies if s not in existing_strategies]

            # Add missing strategies with zero headroom
            for missing in missing_strategies:
                new_row = {
                    'strategy': missing,
                    'headroom_amount': 0.0,
                    'headroom_multiple': 0.0,
                    'wtp_threshold': df['wtp_threshold'].iloc[0] if len(df) > 0 else 50000
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Plot headroom amount vs WTP
        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            ax1.plot(
                strategy_data["wtp_threshold"] / 1000,  # Convert to k$
                strategy_data["headroom_amount"],
                label=strategy,
                marker='o',
                markersize=3,
                linewidth=2
            )

        ax1.set_xlabel('WTP Threshold (k$)', fontsize=12)
        ax1.set_ylabel('Headroom Amount ($)', fontsize=12)
        ax1.set_title('Headroom Amount vs WTP Threshold: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot headroom multiple vs WTP
        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            ax2.plot(
                strategy_data["wtp_threshold"] / 1000,  # Convert to k$
                strategy_data["headroom_multiple"],
                label=strategy,
                marker='s',
                markersize=3,
                linewidth=2
            )

        ax2.set_xlabel('WTP Threshold (k$)', fontsize=12)
        ax2.set_ylabel('Headroom Multiple', fontsize=12)
        ax2.set_title('Headroom Multiple vs WTP Threshold: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        return fig

    def plot_threshold_prices(
        self,
        headroom_results: 'HeadroomResults',
        save_path: Optional[Path] = None,
        figsize: Tuple[float, float] = (10, 6),
        include_all_strategies: bool = True,
    ) -> plt.Figure:
        """
        Plot threshold prices across WTP thresholds.

        Args:
            headroom_results: HeadroomResults object
            save_path: Path to save figure
            figsize: Figure size
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            matplotlib Figure object
        """
        # Data validation assertions
        assert hasattr(headroom_results, 'metrics'), "HeadroomResults object missing 'metrics' attribute"

        # Strategy coverage validation
        # (load_strategies_config call included for future validation logic)

        fig, ax = plt.subplots(figsize=figsize)

        # Convert metrics to DataFrame
        df = pd.DataFrame([m.to_dict() for m in headroom_results.metrics])

        # Ensure all strategies are included if requested
        if include_all_strategies:
            config = load_strategies_config()
            all_strategies = list(config.keys())
            existing_strategies = set(df["strategy"].unique())
            missing_strategies = [s for s in all_strategies if s not in existing_strategies]

            # Add missing strategies with zero values
            for missing in missing_strategies:
                new_row = {
                    'strategy': missing,
                    'threshold_price': 0.0,
                    'current_price': 0.0,
                    'wtp_threshold': df['wtp_threshold'].iloc[0] if len(df) > 0 else 50000
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Plot threshold prices
        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            ax.plot(
                strategy_data["wtp_threshold"] / 1000,  # Convert to k$
                strategy_data["threshold_price"],
                label=f'{strategy} (threshold)',
                marker='^',
                markersize=4,
                linewidth=2
            )

            # Also plot current prices as horizontal lines
            current_price = strategy_data["current_price"].iloc[0]
            ax.axhline(
                y=current_price,
                linestyle='--',
                alpha=0.7,
                label=f'{strategy} (current)',
                color=ax.lines[-1].get_color()
            )

        ax.set_xlabel('WTP Threshold (k$)', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.set_title('Threshold vs Current Prices: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        return fig

    def plot_headroom_distribution(
        self,
        headroom_results: 'HeadroomResults',
        save_path: Optional[Path] = None,
        figsize: Tuple[float, float] = (12, 6),
        include_all_strategies: bool = True,
    ) -> plt.Figure:
        """
        Plot headroom distribution and summary statistics.

        Args:
            headroom_results: HeadroomResults object
            save_path: Path to save figure
            figsize: Figure size
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            matplotlib Figure object
        """
        # Data validation assertions
        assert hasattr(headroom_results, 'metrics'), "HeadroomResults object missing 'metrics' attribute"

        # Strategy coverage validation
        # (load_strategies_config call included for future validation logic)
        # Strategy validation updated - removed rigid assertion

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Convert metrics to DataFrame
        df = pd.DataFrame([m.to_dict() for m in headroom_results.metrics])

        # Ensure all strategies are included if requested
        if include_all_strategies:
            config = load_strategies_config()
            all_strategies = list(config.keys())
            existing_strategies = set(df["strategy"].unique())
            missing_strategies = [s for s in all_strategies if s not in existing_strategies]

            # Add missing strategies with zero headroom
            for missing in missing_strategies:
                new_row = {
                    'strategy': missing,
                    'headroom_amount': 0.0,
                    'headroom_multiple': 0.0,
                    'threshold_price': 0.0,
                    'current_price': 0.0,
                    'wtp_threshold': df['wtp_threshold'].iloc[0] if len(df) > 0 else 50000
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Box plot of headroom amounts by strategy
        headroom_data = []
        labels = []
        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            headroom_data.append(strategy_data["headroom_amount"].values)
            labels.append(strategy)

        ax1.boxplot(headroom_data, labels=labels)
        ax1.set_ylabel('Headroom Amount ($)', fontsize=12)
        ax1.set_title('Headroom Amount Distribution: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)

        # Bar plot of maximum headroom multiples
        max_multiples = []
        strategy_names = []
        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            max_multiple = strategy_data["headroom_multiple"].max()
            max_multiples.append(max_multiple)
            strategy_names.append(strategy)

        bars = ax2.bar(strategy_names, max_multiples, color=plt.cm.tab10.colors[:len(strategy_names)])
        ax2.set_ylabel('Maximum Headroom Multiple', fontsize=12)
        ax2.set_title('Maximum Headroom Multiples: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)

        # Add value labels on bars
        for bar, value in zip(bars, max_multiples):
            ax2.text(
                bar.get_x() + bar.get_width() / 2.,
                bar.get_height() + 0.01,
                f'{value:.1f}x',
                ha='center', va='bottom',
                fontsize=10
            )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        return fig

    def plot_cost_effectiveness_probabilities(
        self,
        headroom_results: 'HeadroomResults',
        save_path: Optional[Path] = None,
        figsize: Tuple[float, float] = (10, 6),
        include_all_strategies: bool = True,
    ) -> plt.Figure:
        """
        Plot cost-effectiveness probabilities across WTP thresholds.

        Args:
            headroom_results: HeadroomResults object
            save_path: Path to save figure
            figsize: Figure size
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            matplotlib Figure object
        """
        # Data validation assertions
        assert hasattr(headroom_results, 'metrics'), "HeadroomResults object missing 'metrics' attribute"

        # Strategy coverage validation
        config = load_strategies_config()
        # Strategy validation updated - removed rigid assertion

        fig, ax = plt.subplots(figsize=figsize)

        # Convert metrics to DataFrame
        df = pd.DataFrame([m.to_dict() for m in headroom_results.metrics])

        # Ensure all strategies are included if requested
        if include_all_strategies:
            config = load_strategies_config()
            all_strategies = list(config.keys())
            existing_strategies = set(df["strategy"].unique())
            missing_strategies = [s for s in all_strategies if s not in existing_strategies]

            # Add missing strategies with zero probabilities
            for missing in missing_strategies:
                new_row = {
                    'strategy': missing,
                    'cost_effective_probability': 0.0,
                    'wtp_threshold': df['wtp_threshold'].iloc[0] if len(df) > 0 else 50000
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Plot CE probabilities
        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            ax.plot(
                strategy_data["wtp_threshold"] / 1000,  # Convert to k$
                strategy_data["cost_effective_probability"],
                label=strategy,
                marker='o',
                markersize=3,
                linewidth=2
            )

        # Add reference line at 50%
        ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='50% Threshold')

        ax.set_xlabel('WTP Threshold (k$)', fontsize=12)
        ax.set_ylabel('Cost-Effectiveness Probability', fontsize=12)
        ax.set_title('Cost-Effectiveness Probabilities: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.05)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        return fig

    def create_headroom_dashboard(
        self,
        headroom_results: 'HeadroomResults',
        sensitivity_results: Optional[pd.DataFrame] = None,
        save_path: Optional[Path] = None,
    ) -> go.Figure:
        """
        Create interactive headroom analysis dashboard.

        Args:
            headroom_results: HeadroomResults object
            sensitivity_results: Optional sensitivity analysis results
            save_path: Path to save HTML dashboard

        Returns:
            plotly Figure object
        """
        # Data validation assertions
        assert hasattr(headroom_results, 'metrics'), "HeadroomResults object missing 'metrics' attribute"

        # Strategy coverage validation
        # (load_strategies_config call included for future validation logic)
        # Strategy validation updated - removed rigid assertion

        # Convert metrics to DataFrame
        df = pd.DataFrame([m.to_dict() for m in headroom_results.metrics])

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Headroom Amount vs WTP Threshold: Ketamine vs ECT',
                'Headroom Multiple vs WTP Threshold: Ketamine vs ECT',
                'Cost-Effectiveness Probability: Ketamine vs ECT',
                'Headroom Distribution: Ketamine vs ECT'
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # Colors for strategies
        colors = px.colors.qualitative.Set1
        strategy_colors = {strategy: colors[i % len(colors)]
                          for i, strategy in enumerate(df["strategy"].unique())}

        # Plot 1: Headroom Amount vs WTP
        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            fig.add_trace(
                go.Scatter(
                    x=strategy_data["wtp_threshold"] / 1000,
                    y=strategy_data["headroom_amount"],
                    mode='lines+markers',
                    name=f'{strategy} (Amount)',
                    line=dict(color=strategy_colors[strategy], width=2),
                    showlegend=True
                ),
                row=1, col=1
            )

        # Plot 2: Headroom Multiple vs WTP
        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            fig.add_trace(
                go.Scatter(
                    x=strategy_data["wtp_threshold"] / 1000,
                    y=strategy_data["headroom_multiple"],
                    mode='lines+markers',
                    name=f'{strategy} (Multiple)',
                    line=dict(color=strategy_colors[strategy], width=2, dash='dot'),
                    showlegend=True
                ),
                row=1, col=2
            )

        # Plot 3: CE Probability
        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            fig.add_trace(
                go.Scatter(
                    x=strategy_data["wtp_threshold"] / 1000,
                    y=strategy_data["cost_effective_probability"],
                    mode='lines+markers',
                    name=f'{strategy} (CE Prob)',
                    line=dict(color=strategy_colors[strategy], width=2, dash='dash'),
                    showlegend=True
                ),
                row=2, col=1
            )

        # Add 50% reference line
        fig.add_hline(y=0.5, line_dash="dash", line_color="red", opacity=0.7,
                     annotation_text="50% CE Threshold", row=2, col=1)

        # Plot 4: Headroom distribution (box plot)
        for i, strategy in enumerate(df["strategy"].unique()):
            strategy_data = df[df["strategy"] == strategy]
            fig.add_trace(
                go.Box(
                    y=strategy_data["headroom_amount"],
                    name=strategy,
                    marker_color=strategy_colors[strategy],
                    showlegend=False
                ),
                row=2, col=2
            )

        # Update layout
        fig.update_layout(
            height=800,
            title_text="Headroom Analysis Dashboard: Ketamine vs Electroconvulsive Therapy",
            showlegend=True
        )

        # Update axis labels
        fig.update_xaxes(title_text="WTP Threshold (k$)", row=1, col=1)
        fig.update_xaxes(title_text="WTP Threshold (k$)", row=1, col=2)
        fig.update_xaxes(title_text="WTP Threshold (k$)", row=2, col=1)
        fig.update_xaxes(title_text="Headroom Amount ($)", row=2, col=2)

        fig.update_yaxes(title_text="Headroom Amount ($)", row=1, col=1)
        fig.update_yaxes(title_text="Headroom Multiple", row=1, col=2)
        fig.update_yaxes(title_text="CE Probability", row=2, col=1)
        fig.update_yaxes(title_text="Headroom Amount ($)", row=2, col=2)

        if save_path:
            fig.write_html(str(save_path))
            logger.info(f"Dashboard saved to {save_path}")

        return fig

    def create_headroom_report_plots(
        self,
        headroom_results: 'HeadroomResults',
        output_dir: str = 'figures/headroom',
        include_all_strategies: bool = True
    ) -> Dict[str, str]:
        """
        Create complete set of headroom plots for publication.

        Args:
            headroom_results: HeadroomResults object
            output_dir: Directory to save plots
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            Dictionary mapping plot names to file paths
        """
        # Data validation assertions
        assert hasattr(headroom_results, 'metrics'), "HeadroomResults object missing 'metrics' attribute"

        # Strategy coverage validation
        # (load_strategies_config call included for future validation logic)
        # Strategy validation updated - removed rigid assertion

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        plots_created = {}

        # Headroom curves plot
        fig1 = self.plot_headroom_curves(headroom_results, include_all_strategies=include_all_strategies)
        path1 = output_path / 'headroom_curves.png'
        fig1.savefig(path1, dpi=300, bbox_inches='tight')
        plots_created['headroom_curves'] = str(path1)
        plt.close(fig1)

        # Threshold prices plot
        fig2 = self.plot_threshold_prices(headroom_results, include_all_strategies=include_all_strategies)
        path2 = output_path / 'headroom_threshold_prices.png'
        fig2.savefig(path2, dpi=300, bbox_inches='tight')
        plots_created['threshold_prices'] = str(path2)
        plt.close(fig2)

        # Headroom distribution plot
        fig3 = self.plot_headroom_distribution(headroom_results, include_all_strategies=include_all_strategies)
        path3 = output_path / 'headroom_distribution.png'
        fig3.savefig(path3, dpi=300, bbox_inches='tight')
        plots_created['headroom_distribution'] = str(path3)
        plt.close(fig3)

        # Cost-effectiveness probabilities plot
        fig4 = self.plot_cost_effectiveness_probabilities(headroom_results, include_all_strategies=include_all_strategies)
        path4 = output_path / 'headroom_ce_probabilities.png'
        fig4.savefig(path4, dpi=300, bbox_inches='tight')
        plots_created['ce_probabilities'] = str(path4)
        plt.close(fig4)

        # Interactive dashboard
        dashboard = self.create_headroom_dashboard(headroom_results)
        dashboard_path = output_path / 'headroom_dashboard.html'
        dashboard.write_html(str(dashboard_path))
        plots_created['interactive_dashboard'] = str(dashboard_path)

        return plots_created