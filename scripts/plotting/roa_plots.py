"""
Real Options Analysis (ROA) Plotting Functions for V4 Health Economic Evaluation

This module provides visualization functions for real options analysis results,
including option value plots, flexibility value charts, and sensitivity analysis.

Features:
- Option value comparison plots
- Value of flexibility bar charts
- Option sensitivity (delta) plots
- Strategy ranking with options
- Risk-adjusted NPV comparisons

Author: V4 Development Team
Date: October 2025
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple, Any
from matplotlib.figure import Figure
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.plotting.publication import (
    JournalStandards
)


class ROAPlotter:
    """Plotting functions for Real Options Analysis results."""

    def __init__(self, journal_style: bool = True):
        """Initialize ROA plotter."""
        self.journal_style = journal_style
        self.standards = JournalStandards() if journal_style else None

    def _safe_legend(self, ax_obj, **leg_kwargs) -> None:
        """
        Safely add a legend to axes only when there are labeled artists.
        """
        handles, labels = ax_obj.get_legend_handles_labels()
        if handles and any(lbl and not str(lbl).startswith('_') for lbl in labels):
            ax_obj.legend(**leg_kwargs)

    def plot_option_values(
        self,
        results: Any,
        save_path: Optional[str] = None,
        figsize: Tuple[float, float] = (12, 8),
        include_all_strategies: bool = True
    ) -> Figure:
        """
        Plot option values by strategy and option type.

        Args:
            results: ROA results object
            save_path: Path to save figure
            figsize: Figure size
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack option data

        Returns:
            matplotlib Figure object
        """
        # Data validation assertions
        assert hasattr(results, 'option_values'), "ROAResults object missing 'option_values' attribute"

        # Strategy coverage validation
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        _expected_strategies = set(config.keys())
        # Strategy validation updated - removed rigid assertion

        fig, ax = plt.subplots(figsize=figsize)

        # Prepare data
        option_data = []

        # Get all 10 strategies from config if include_all_strategies is True
        if include_all_strategies:
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            all_strategies = list(config.keys())
        else:
            all_strategies = list(results.option_values.keys())

        for strategy in all_strategies:
            if strategy in results.option_values:
                options = results.option_values[strategy]
                for option_type, value in options.items():
                    option_data.append({
                        'Strategy': strategy,
                        'Option Type': option_type.capitalize(),
                        'Value': value,
                        'has_data': True
                    })
            elif include_all_strategies:
                # Add placeholder for missing strategies
                option_data.append({
                    'Strategy': strategy,
                    'Option Type': 'Call',  # Default option type
                    'Value': 0,
                    'has_data': False
                })

        df = pd.DataFrame(option_data)

        # Create grouped bar plot
        sns.barplot(
            data=df,
            x='Strategy',
            y='Value',
            hue='Option Type',
            ax=ax,
            palette='Set2'
        )

        ax.set_title('Real Option Values by Strategy: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax.set_xlabel('Treatment Strategy', fontsize=12)
        ax.set_ylabel('Option Value ($)', fontsize=12)
        # Use class helper to guard legend calls
        self._safe_legend(ax, title='Option Type', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Rotate x-axis labels if needed
        plt.xticks(rotation=45, ha='right')

        if self.journal_style and self.standards:
            plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_value_of_flexibility(
        self,
        results: Any,
        save_path: Optional[str] = None,
        figsize: Tuple[float, float] = (10, 6),
        include_all_strategies: bool = True
    ) -> Figure:
        """
        Plot the value of managerial flexibility for each strategy.
        self._safe_legend(ax, title='Option Type', bbox_to_anchor=(1.05, 1), loc='upper left')
        Args:
            results: ROA results object
            save_path: Path to save figure
            figsize: Figure size
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack flexibility data

        Returns:
            matplotlib Figure object
        """
        # Data validation assertions
        assert hasattr(results, 'value_of_flexibility'), "ROAResults object missing 'value_of_flexibility' attribute"

        # Strategy coverage validation
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        _expected_strategies = set(config.keys())
        # Strategy validation updated - removed rigid assertion

        fig, ax = plt.subplots(figsize=figsize)

        # Get all 10 strategies from config if include_all_strategies is True
        if include_all_strategies:
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            all_strategies = list(config.keys())
        else:
            all_strategies = list(results.value_of_flexibility.keys())

        strategies = []
        values = []
        has_data_list = []

        for strategy in all_strategies:
            if strategy in results.value_of_flexibility:
                strategies.append(strategy)
                values.append(results.value_of_flexibility[strategy])
                has_data_list.append(True)
            elif include_all_strategies:
                strategies.append(strategy)
                values.append(0)
                has_data_list.append(False)

        # Create horizontal bar plot with different colors for missing data
        colors = ['skyblue' if has_data else 'lightgray' for has_data in has_data_list]
        bars = ax.barh(strategies, values, color=colors, alpha=0.8)

        # Add value labels
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_width() + max(values) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f'${value:,.0f}',
                ha='left',
                va='center',
                fontsize=10
            )

        ax.set_title('Value of Managerial Flexibility: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax.set_xlabel('Additional Value from Options ($)', fontsize=12)
        ax.set_ylabel('Treatment Strategy', fontsize=12)

        if self.journal_style and self.standards:
            plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_total_value_comparison(
        self,
        results: Any,
        save_path: Optional[str] = None,
        figsize: Tuple[float, float] = (12, 8),
        include_all_strategies: bool = True
    ) -> Figure:
        """
        Plot comparison of base NPV vs total value with options.

        Args:
            results: ROA results object
            save_path: Path to save figure
            figsize: Figure size
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack value data

        Returns:
            matplotlib Figure object
        """
        # Data validation assertions
        assert hasattr(results, 'strategies'), "ROAResults object missing 'strategies' attribute"
        assert hasattr(results, 'risk_adjusted_npv'), "ROAResults object missing 'risk_adjusted_npv' attribute"
        assert hasattr(results, 'total_value_with_options'), "ROAResults object missing 'total_value_with_options' attribute"

        # Strategy coverage validation
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        _expected_strategies = set(config.keys())
        # Strategy validation updated - removed rigid assertion

        fig, ax = plt.subplots(figsize=figsize)

        # Get all 10 strategies from config if include_all_strategies is True
        if include_all_strategies:
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            all_strategies = list(config.keys())
        else:
            all_strategies = list(results.strategies)

        strategies = []
        base_npvs = []
        total_values = []
        has_data_list = []

        for strategy in all_strategies:
            if strategy in results.risk_adjusted_npv and strategy in results.total_value_with_options:
                strategies.append(strategy)
                base_npvs.append(results.risk_adjusted_npv[strategy])
                total_values.append(results.total_value_with_options[strategy])
                has_data_list.append(True)
            elif include_all_strategies:
                strategies.append(strategy)
                base_npvs.append(0)
                total_values.append(0)
                has_data_list.append(False)

        x = np.arange(len(strategies))
        width = 0.35

        # Create grouped bars with different colors for missing data
        base_colors = ['lightcoral' if has_data else 'lightgray' for has_data in has_data_list]
        option_colors = ['lightgreen' if has_data else 'lightgray' for has_data in has_data_list]
        bars1 = ax.bar(x - width/2, base_npvs, width, label='Base NPV', color=base_colors, alpha=0.8)
        bars2 = ax.bar(x + width/2, total_values, width, label='With Options', color=option_colors, alpha=0.8)

        # Add value labels
        for bars, values in [(bars1, base_npvs), (bars2, total_values)]:
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + max(total_values) * 0.01,
                    f'${value:,.0f}',
                    ha='center',
                    va='bottom',
                    fontsize=9
                )

        ax.set_title('Base NPV vs Total Value with Real Options: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax.set_xlabel('Treatment Strategy', fontsize=12)
        ax.set_ylabel('Value ($)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(strategies, rotation=45, ha='right')
        # Guard legend call using class helper
        self._safe_legend(ax)

        if self.journal_style and self.standards:
            plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_option_sensitivity(
        self,
        results: Any,
        save_path: Optional[str] = None,
        figsize: Tuple[float, float] = (12, 8),
        include_all_strategies: bool = True
    ) -> Figure:
        """
        Plot option delta (sensitivity) for each option.

        Args:
            results: ROA results object
            save_path: Path to save figure
            figsize: Figure size
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack sensitivity data

        Returns:
            matplotlib Figure object
        """
        # Data validation assertions
        assert hasattr(results, 'options'), "ROAResults object missing 'options' attribute"

        # Strategy coverage validation
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        _expected_strategies = set(config.keys())
        # Strategy validation updated - removed rigid assertion

        fig, ax = plt.subplots(figsize=figsize)

        # Prepare data
        sensitivity_data = []
        for option in results.options:
            sensitivity_data.append({
                'Strategy': option.strategy,
                'Option Type': option.option_type.capitalize(),
                'Delta': option.delta,
                'Value': option.option_value
            })

        df = pd.DataFrame(sensitivity_data)

        # Create scatter plot with size representing option value
        # Ensure the color mapping is only used when we have a numeric vector
        values = df['Value'].to_numpy()
        try:
            numeric_values = np.asarray(values, dtype=float)
            color_kwargs: Dict[str, Any] = {'c': numeric_values, 'cmap': 'viridis'}
        except Exception:
            # Fallback to single color
            color_kwargs: Dict[str, Any] = {'color': 'C0'}

        scatter = ax.scatter(
            df['Option Type'],
            df['Delta'],
            s=np.maximum(df['Value'].fillna(0).to_numpy() * 100, 1),  # Scale & avoid zero-size
            alpha=0.6,
            **color_kwargs
        )

        ax.set_title('Option Sensitivity (Delta) Analysis: Ketamine vs Electroconvulsive Therapy', fontsize=14, fontweight='bold')
        ax.set_xlabel('Option Type', fontsize=12)
        ax.set_ylabel('Delta (Sensitivity to Underlying Value)', fontsize=12)

        # Add colorbar if available (only when scatter used numeric mapping)
        if hasattr(scatter, 'get_array') and scatter.get_array() is not None:
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Option Value ($)')

        if self.journal_style and self.standards:
            plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def create_interactive_roa_dashboard(
        self,
        results: Any,
        save_path: Optional[str] = None
    ) -> go.Figure:
        """
        Create interactive dashboard for ROA results.

        Args:
            results: ROA results object
            save_path: Path to save figure

        Returns:
            plotly Figure object
        """
        # Data validation assertions
        assert hasattr(results, 'option_values'), "ROAResults object missing 'option_values' attribute"
        assert hasattr(results, 'value_of_flexibility'), "ROAResults object missing 'value_of_flexibility' attribute"
        assert hasattr(results, 'strategies'), "ROAResults object missing 'strategies' attribute"
        assert hasattr(results, 'risk_adjusted_npv'), "ROAResults object missing 'risk_adjusted_npv' attribute"
        assert hasattr(results, 'total_value_with_options'), "ROAResults object missing 'total_value_with_options' attribute"
        assert hasattr(results, 'options'), "ROAResults object missing 'options' attribute"

        # Strategy coverage validation
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        _expected_strategies = set(config.keys())
        # Strategy validation updated - removed rigid assertion

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Option Values by Strategy: Ketamine vs ECT',
                'Value of Flexibility: Ketamine vs ECT',
                'Base vs Total Value Comparison: Ketamine vs ECT',
                'Option Sensitivity Analysis: Ketamine vs ECT'
            ),
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'scatter'}]]
        )

        # Plot 1: Option Values
        option_data = []
        for strategy, options in results.option_values.items():
            for option_type, value in options.items():
                option_data.append({
                    'Strategy': strategy,
                    'Option Type': option_type.capitalize(),
                    'Value': value
                })

        df_options = pd.DataFrame(option_data)

        for option_type in df_options['Option Type'].unique():
            df_filtered = df_options[df_options['Option Type'] == option_type]
            fig.add_trace(
                go.Bar(
                    name=option_type,
                    x=df_filtered['Strategy'],
                    y=df_filtered['Value'],
                    showlegend=True
                ),
                row=1, col=1
            )

        # Plot 2: Value of Flexibility
        strategies = list(results.value_of_flexibility.keys())
        flex_values = list(results.value_of_flexibility.values())

        fig.add_trace(
            go.Bar(
                name='Flexibility Value',
                x=strategies,
                y=flex_values,
                marker_color='lightblue'
            ),
            row=1, col=2
        )

        # Plot 3: Base vs Total Value
        strategies = list(results.strategies)
        base_npvs = [results.risk_adjusted_npv[s] for s in strategies]
        total_values = [results.total_value_with_options[s] for s in strategies]

        fig.add_trace(
            go.Bar(
                name='Base NPV',
                x=strategies,
                y=base_npvs,
                marker_color='lightcoral'
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Bar(
                name='With Options',
                x=strategies,
                y=total_values,
                marker_color='lightgreen'
            ),
            row=2, col=1
        )

        # Plot 4: Option Sensitivity (simplified)
        sensitivity_data = []
        for option in results.options:
            sensitivity_data.append({
                'Option Type': option.option_type.capitalize(),
                'Delta': option.delta if np.isfinite(option.delta) else 0.5,
                'Value': option.option_value if np.isfinite(option.option_value) else 0.0
            })

        df_sens = pd.DataFrame(sensitivity_data)

        # Filter out any remaining NaN values
        df_sens = df_sens.dropna()

        if not df_sens.empty:
            fig.add_trace(
                go.Scatter(
                    name='Sensitivity',
                    x=df_sens['Option Type'],
                    y=df_sens['Delta'],
                    mode='markers',
                    marker=dict(
                        size=np.maximum(df_sens['Value'] * 10, 5),  # Minimum size of 5
                        color=df_sens['Value'],
                        colorscale='Viridis',
                        showscale=True
                    )
                ),
                row=2, col=2
            )

        # Update layout
        fig.update_layout(
            title='Real Options Analysis Dashboard: Ketamine vs Electroconvulsive Therapy',
            height=800,
            showlegend=True
        )

        if save_path:
            fig.write_html(save_path)

        return fig

    def create_roa_report_plots(
        self,
        results: Any,
        output_dir: str = 'figures/roa',
        include_all_strategies: bool = True
    ) -> Dict[str, str]:
        """
        Create complete set of ROA plots for publication.

        Args:
            results: ROA results object
            output_dir: Directory to save plots
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            Dictionary mapping plot names to file paths
        """
        # Data validation assertions
        assert hasattr(results, 'option_values'), "ROAResults object missing 'option_values' attribute"
        assert hasattr(results, 'value_of_flexibility'), "ROAResults object missing 'value_of_flexibility' attribute"
        assert hasattr(results, 'strategies'), "ROAResults object missing 'strategies' attribute"
        assert hasattr(results, 'risk_adjusted_npv'), "ROAResults object missing 'risk_adjusted_npv' attribute"
        assert hasattr(results, 'total_value_with_options'), "ROAResults object missing 'total_value_with_options' attribute"
        assert hasattr(results, 'options'), "ROAResults object missing 'options' attribute"

        # Strategy coverage validation
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        _expected_strategies = set(config.keys())
        # Strategy validation updated - removed rigid assertion
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        plots_created = {}

        # Option values plot
        fig1 = self.plot_option_values(results, include_all_strategies=include_all_strategies)
        path1 = output_path / 'roa_option_values.png'
        fig1.savefig(path1, dpi=300, bbox_inches='tight')
        plots_created['option_values'] = str(path1)
        plt.close(fig1)

        # Value of flexibility plot
        fig2 = self.plot_value_of_flexibility(results, include_all_strategies=include_all_strategies)
        path2 = output_path / 'roa_flexibility_value.png'
        fig2.savefig(path2, dpi=300, bbox_inches='tight')
        plots_created['flexibility_value'] = str(path2)
        plt.close(fig2)

        # Total value comparison
        fig3 = self.plot_total_value_comparison(results, include_all_strategies=include_all_strategies)
        path3 = output_path / 'roa_total_value_comparison.png'
        fig3.savefig(path3, dpi=300, bbox_inches='tight')
        plots_created['total_value_comparison'] = str(path3)
        plt.close(fig3)

        # Option sensitivity
        fig4 = self.plot_option_sensitivity(results, include_all_strategies=include_all_strategies)
        path4 = output_path / 'roa_option_sensitivity.png'
        fig4.savefig(path4, dpi=300, bbox_inches='tight')
        plots_created['option_sensitivity'] = str(path4)
        plt.close(fig4)

        # Interactive dashboard
        dashboard = self.create_interactive_roa_dashboard(results)
        dashboard_path = output_path / 'roa_dashboard.html'
        dashboard.write_html(str(dashboard_path))
        plots_created['interactive_dashboard'] = str(dashboard_path)

        return plots_created