"""
Plotting functions for Return on Investment (ROI) Analysis results.

This module provides comprehensive visualization capabilities for ROI analysis,
including benefit-cost ratio plots, payback period analysis, ROI percentage
comparisons, and interactive dashboards.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import matplotlib.pyplot as plt
from analysis.plotting.publication import _get_cmap
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.plotting.publication import (
    JournalStandards
)

logger = logging.getLogger(__name__)


class ROIPlotter:
    """
    Plotting functions for ROI analysis results.

    Provides publication-quality visualizations for ROI metrics including
    benefit-cost ratios, payback periods, ROI percentages, and break-even analysis.
    """

    def __init__(self, journal_style: bool = True):
        """
        Initialize ROI plotter.

        Args:
            journal_style: Whether to use journal formatting standards
        """
        self.journal_style = journal_style
        self.standards = JournalStandards() if journal_style else None
        logger.info("Initialized ROI plotter")

    def plot_benefit_cost_ratios(
        self,
        roi_results: Dict,
        save_path: Optional[Path] = None,
        figsize: Tuple[float, float] = (10, 6),
        include_all_strategies: bool = True,
    ) -> plt.Figure:
        """
        Plot benefit-cost ratios for all strategies.

        Args:
            roi_results: ROI analysis results dictionary
            save_path: Optional path to save figure
            figsize: Figure size (width, height)
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            Matplotlib figure object
        """
        # Data validation assertions
        assert isinstance(roi_results, dict), "roi_results must be a dictionary"
        assert "metrics" in roi_results, "roi_results missing 'metrics' key"

        # Strategy coverage validation
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        expected_strategies = set(config.keys())
        assert len(expected_strategies) == 12, f"Expected 12 strategies from config, got {len(expected_strategies)}"

        logger.info("Plotting benefit-cost ratios")

        metrics = roi_results["metrics"]
        strategies = [m["strategy"] for m in metrics]
        ratios = [m["benefit_cost_ratio"] for m in metrics]

        # Ensure all strategies are included if requested
        if include_all_strategies:
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            all_strategies = list(config.keys())
            existing_strategies = set(strategies)
            missing_strategies = [s for s in all_strategies if s not in existing_strategies]

            # Add missing strategies with zero values
            for missing in missing_strategies:
                strategies.append(missing)
                ratios.append(0.0)

        fig, ax = plt.subplots(figsize=figsize)

        # Use gray color for missing strategies
        colors = []
        cmap = _get_cmap('tab10')
        sampled = cmap(np.linspace(0, 1, max(10, len(strategies))))
        for idx, strategy in enumerate(strategies):
            if strategy in [m["strategy"] for m in metrics]:
                colors.append(tuple(sampled[idx % len(sampled)]))
            else:
                colors.append('gray')

        _bars = ax.bar(strategies, ratios, color=colors)

        # Add value labels on bars (skip for zero values)
        for bar, ratio, strategy in zip(_bars, ratios, strategies):
            if ratio > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                       f'{ratio:.2f}', ha='center', va='bottom', fontsize=10)

        ax.set_xlabel('Treatment Strategy', fontsize=12)
        ax.set_ylabel('Benefit-Cost Ratio', fontsize=12)
        ax.set_title('Benefit-Cost Ratios by Strategy', fontsize=14, fontweight='bold')

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')

        # Add reference line at 1.0 (break-even)
        ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Break-even (BCR = 1.0)')
        ax.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        return fig

    def plot_roi_percentages(
        self,
        roi_results: Dict,
        save_path: Optional[Path] = None,
        figsize: Tuple[float, float] = (10, 6),
        include_all_strategies: bool = True,
    ) -> plt.Figure:
        """
        Plot ROI percentages for all strategies.

        Args:
            roi_results: ROI analysis results dictionary
            save_path: Optional path to save figure
            figsize: Figure size (width, height)
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            Matplotlib figure object
        """
        # Data validation assertions
        assert isinstance(roi_results, dict), "roi_results must be a dictionary"
        assert "metrics" in roi_results, "roi_results missing 'metrics' key"

        # Strategy coverage validation
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        expected_strategies = set(config.keys())
        assert len(expected_strategies) == 12, f"Expected 12 strategies from config, got {len(expected_strategies)}"

        logger.info("Plotting ROI percentages")

        metrics = roi_results["metrics"]
        strategies = [m["strategy"] for m in metrics]
        roi_pcts = [m["roi_percentage"] for m in metrics]

        # Ensure all strategies are included if requested
        if include_all_strategies:
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            all_strategies = list(config.keys())
            existing_strategies = set(strategies)
            missing_strategies = [s for s in all_strategies if s not in existing_strategies]

            # Add missing strategies with zero values
            for missing in missing_strategies:
                strategies.append(missing)
                roi_pcts.append(0.0)

        fig, ax = plt.subplots(figsize=figsize)

        # Use gray color for missing strategies, green/red for positive/negative ROI
        colors = []
        for i, (strategy, pct) in enumerate(zip(strategies, roi_pcts)):
            if strategy in [m["strategy"] for m in metrics]:
                colors.append('green' if pct > 0 else 'red')
            else:
                colors.append('gray')

        _bars = ax.bar(strategies, roi_pcts, color=colors)

        # Add value labels on bars
        for bar, pct in zip(_bars, roi_pcts):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + (1 if height >= 0 else -1) * max(abs(h) for h in roi_pcts) * 0.01,
                f'{pct:.1f}%',
                ha='center', va='bottom' if height >= 0 else 'top',
                fontsize=10
            )

        ax.set_xlabel('Treatment Strategy', fontsize=12)
        ax.set_ylabel('ROI Percentage (%)', fontsize=12)
        ax.set_title('Return on Investment by Strategy', fontsize=14, fontweight='bold')

        # Add reference line at 0% (break-even)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5, label='Break-even (ROI = 0%)')
        ax.legend()

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        return fig

    def plot_payback_periods(
        self,
        roi_results: Dict,
        save_path: Optional[Path] = None,
        figsize: Tuple[float, float] = (10, 6),
        include_all_strategies: bool = True,
    ) -> plt.Figure:
        """
        Plot payback periods for strategies with positive ROI.

        Args:
            roi_results: ROI analysis results dictionary
            save_path: Optional path to save figure
            figsize: Figure size (width, height)
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            Matplotlib figure object
        """
        # Data validation assertions
        assert isinstance(roi_results, dict), "roi_results must be a dictionary"
        assert "metrics" in roi_results, "roi_results missing 'metrics' key"

        # Strategy coverage validation
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        expected_strategies = set(config.keys())
        assert len(expected_strategies) == 12, f"Expected 12 strategies from config, got {len(expected_strategies)}"
        logger.info("Plotting payback periods")

        metrics = roi_results["metrics"]
        strategies = [m["strategy"] for m in metrics]
        payback_periods = [m["payback_period_years"] for m in metrics]

        # Ensure all strategies are included if requested
        if include_all_strategies:
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            all_strategies = list(config.keys())
            existing_strategies = set(strategies)
            missing_strategies = [s for s in all_strategies if s not in existing_strategies]

            # Add missing strategies with zero values (no payback period)
            for missing in missing_strategies:
                strategies.append(missing)
                payback_periods.append(0.0)

        fig, ax = plt.subplots(figsize=figsize)

        # Use gray color for missing strategies
        colors = []
        cmap = _get_cmap('tab10')
        sampled = cmap(np.linspace(0, 1, max(10, len(strategies))))
        for idx, strategy in enumerate(strategies):
            if strategy in [m["strategy"] for m in metrics]:
                colors.append(tuple(sampled[idx % len(sampled)]))
            else:
                colors.append('gray')

        _bars = ax.bar(strategies, payback_periods, color=colors)

        # Add value labels on bars (skip for zero values)
        for bar, period, strategy in zip(_bars, payback_periods, strategies):
            if period > 0:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height + 0.1,
                    f'{period:.1f} yrs',
                    ha='center', va='bottom',
                    fontsize=10
                )

        ax.set_xlabel('Treatment Strategy', fontsize=12)
        ax.set_ylabel('Payback Period (Years)', fontsize=12)
        ax.set_title('Payback Periods by Strategy', fontsize=14, fontweight='bold')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        return fig

    def plot_break_even_probabilities(
        self,
        roi_results: Dict,
        save_path: Optional[Path] = None,
        figsize: Tuple[float, float] = (10, 6),
        include_all_strategies: bool = True,
    ) -> plt.Figure:
        """
        Plot break-even probabilities for all strategies.

        Args:
            roi_results: ROI analysis results dictionary
            save_path: Optional path to save figure
            figsize: Figure size (width, height)
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            Matplotlib figure object
        """
        # Data validation assertions
        assert isinstance(roi_results, dict), f"roi_results must be a dictionary, got {type(roi_results)}"
        assert "metrics" in roi_results, "roi_results must contain 'metrics' key"
        assert isinstance(roi_results["metrics"], list), f"roi_results['metrics'] must be a list, got {type(roi_results['metrics'])}"
        assert len(roi_results["metrics"]) > 0, "roi_results['metrics'] cannot be empty"

        # Validate strategy coverage
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        expected_strategies = set(config.keys())
        assert len(expected_strategies) == 12, f"Expected 12 strategies from config, got {len(expected_strategies)}"

        available_strategies = set(m.get("strategy") for m in roi_results["metrics"] if isinstance(m, dict) and "strategy" in m)
        assert available_strategies.issubset(expected_strategies), f"Available strategies {available_strategies} not subset of expected {expected_strategies}"

        logger.info("Plotting break-even probabilities")

        metrics = roi_results["metrics"]
        strategies = [m["strategy"] for m in metrics]
        probabilities = [m["break_even_probability"] for m in metrics]

        # Ensure all strategies are included if requested
        if include_all_strategies:
            from analysis.core.io import load_strategies_config
            config = load_strategies_config()
            all_strategies = list(config.keys())
            existing_strategies = set(strategies)
            missing_strategies = [s for s in all_strategies if s not in existing_strategies]

            # Add missing strategies with zero values
            for missing in missing_strategies:
                strategies.append(missing)
                probabilities.append(0.0)

        fig, ax = plt.subplots(figsize=figsize)

        # Use gray color for missing strategies
        colors = []
        cmap = _get_cmap('tab10')
        sampled = cmap(np.linspace(0, 1, max(10, len(strategies))))
        for idx, strategy in enumerate(strategies):
            if strategy in [m["strategy"] for m in metrics]:
                colors.append(tuple(sampled[idx % len(sampled)]))
            else:
                colors.append('gray')

        _bars = ax.bar(strategies, probabilities, color=colors)

        # Add value labels on bars
        for bar, prob in zip(_bars, probabilities):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + 0.01,
                f'{prob:.1%}',
                ha='center', va='bottom',
                fontsize=10
            )

        ax.set_xlabel('Treatment Strategy', fontsize=12)
        ax.set_ylabel('Break-even Probability', fontsize=12)
        ax.set_title('Break-even Probabilities by Strategy', fontsize=14, fontweight='bold')

        # Add reference line at 50%
        ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='50% Threshold')
        ax.legend()

        ax.set_ylim(0, 1.05)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        return fig

    def create_roi_dashboard(
        self,
        roi_results: Dict,
        save_path: Optional[Path] = None,
    ) -> go.Figure:
        """
        Create interactive ROI dashboard with multiple subplots.

        Args:
            roi_results: ROI analysis results dictionary
            save_path: Optional path to save HTML dashboard

        Returns:
            Plotly figure object
        """
        # Data validation assertions
        assert isinstance(roi_results, dict), f"roi_results must be a dictionary, got {type(roi_results)}"
        assert "metrics" in roi_results, "roi_results must contain 'metrics' key"
        assert isinstance(roi_results["metrics"], list), f"roi_results['metrics'] must be a list, got {type(roi_results['metrics'])}"
        assert len(roi_results["metrics"]) > 0, "roi_results['metrics'] cannot be empty"

        # Validate strategy coverage
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        expected_strategies = set(config.keys())
        assert len(expected_strategies) == 12, f"Expected 12 strategies from config, got {len(expected_strategies)}"

        available_strategies = set(m.get("strategy") for m in roi_results["metrics"] if isinstance(m, dict) and "strategy" in m)
        assert available_strategies.issubset(expected_strategies), f"Available strategies {available_strategies} not subset of expected {expected_strategies}"

        logger.info("Creating ROI dashboard")

        metrics = roi_results["metrics"]
        strategies = [m["strategy"] for m in metrics]

        # Create subplot figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Benefit-Cost Ratios',
                'ROI Percentages',
                'Break-even Probabilities',
                'Payback Periods'
            ),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )

        # Benefit-Cost Ratios
        bcr_values = [m["benefit_cost_ratio"] for m in metrics]
        fig.add_trace(
            go.Bar(x=strategies, y=bcr_values, name="BCR",
                   marker_color='lightblue'),
            row=1, col=1
        )
        fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                     annotation_text="Break-even", row=1, col=1)

        # ROI Percentages
        roi_values = [m["roi_percentage"] for m in metrics]
        colors = ['green' if pct > 0 else 'red' for pct in roi_values]
        fig.add_trace(
            go.Bar(x=strategies, y=roi_values, name="ROI %",
                   marker_color=colors),
            row=1, col=2
        )
        fig.add_hline(y=0, line_dash="dash", line_color="black",
                     annotation_text="Break-even", row=1, col=2)

        # Break-even Probabilities
        bep_values = [m["break_even_probability"] for m in metrics]
        fig.add_trace(
            go.Bar(x=strategies, y=bep_values, name="Break-even Prob",
                   marker_color='lightgreen'),
            row=2, col=1
        )
        fig.add_hline(y=0.5, line_dash="dash", line_color="orange",
                     annotation_text="50% Threshold", row=2, col=1)

        # Payback Periods (filter valid values)
        valid_payback = [(s, m["payback_period_years"]) for s, m in zip(strategies, metrics)
                        if m["payback_period_years"] is not None]
        if valid_payback:
            pb_strategies, pb_values = zip(*valid_payback)
            fig.add_trace(
                go.Bar(x=list(pb_strategies), y=list(pb_values), name="Payback Period",
                       marker_color='orange'),
                row=2, col=2
            )
            # Add time horizon reference line if metadata available
            if "analysis_metadata" in roi_results and "time_horizon_years" in roi_results["analysis_metadata"]:
                horizon = roi_results["analysis_metadata"]["time_horizon_years"]
                fig.add_hline(y=horizon, line_dash="dash", line_color="red",
                             annotation_text=f"Horizon ({horizon} yrs)", row=2, col=2)

        # Update layout
        fig.update_layout(
            height=800,
            title_text="ROI Analysis Dashboard",
            showlegend=False
        )

        # Update x-axis labels
        fig.update_xaxes(tickangle=45)

        if save_path:
            fig.write_html(str(save_path))
            logger.info(f"Dashboard saved to {save_path}")

        return fig

    def plot_roi_summary_stats(
        self,
        roi_results: Dict,
        save_path: Optional[Path] = None,
        figsize: Tuple[float, float] = (12, 8),
    ) -> plt.Figure:
        """
        Plot summary statistics across all ROI metrics.

        Args:
            roi_results: ROI analysis results dictionary
            save_path: Optional path to save figure
            figsize: Figure size (width, height)

        Returns:
            Matplotlib figure object
        """
        # Data validation assertions
        assert isinstance(roi_results, dict), f"roi_results must be a dictionary, got {type(roi_results)}"
        assert "summary_stats" in roi_results, "roi_results must contain 'summary_stats' key"
        assert isinstance(roi_results["summary_stats"], dict), f"roi_results['summary_stats'] must be a dict, got {type(roi_results['summary_stats'])}"

        logger.info("Plotting ROI summary statistics")

        summary_stats = roi_results["summary_stats"]

        if not summary_stats:
            logger.warning("No summary statistics available")
            return plt.figure()

        # Extract metrics and their stats
        metrics = list(summary_stats.keys())
        means = [summary_stats[m]["mean"] for m in metrics]
        stds = [summary_stats[m]["std"] for m in metrics]

        fig, ax = plt.subplots(figsize=figsize)

        # Create bar plot with error bars
        cmap = _get_cmap('tab10')
        sampled = cmap(np.linspace(0, 1, max(10, len(metrics))))
        colors = [tuple(sampled[i % len(sampled)]) for i in range(len(metrics))]
        _bars = ax.bar(metrics, means, yerr=stds,
                      capsize=5, color=colors)

        ax.set_xlabel('ROI Metric', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title('ROI Metrics Summary Statistics', fontsize=14, fontweight='bold')

        # Format metric names
        formatted_labels = [m.replace('_', ' ').title() for m in metrics]
        ax.set_xticklabels(formatted_labels, rotation=45, ha='right')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        return fig

    def create_roi_report_plots(
        self,
        roi_results: Dict,
        output_dir: str = 'figures/roi',
        include_all_strategies: bool = True
    ) -> Dict[str, str]:
        """
        Create complete set of ROI plots for publication.

        Args:
            roi_results: ROI analysis results dictionary
            output_dir: Directory to save plots
            include_all_strategies: If True, ensure all 10 treatment strategies are included
                                   in plots even if they lack data

        Returns:
            Dictionary mapping plot names to file paths
        """
        # Data validation assertions
        assert isinstance(roi_results, dict), f"roi_results must be a dictionary, got {type(roi_results)}"
        assert "metrics" in roi_results, "roi_results must contain 'metrics' key"
        assert isinstance(roi_results["metrics"], list), f"roi_results['metrics'] must be a list, got {type(roi_results['metrics'])}"
        assert len(roi_results["metrics"]) > 0, "roi_results['metrics'] cannot be empty"

        # Validate strategy coverage
        from analysis.core.io import load_strategies_config
        config = load_strategies_config()
        expected_strategies = set(config.keys())
        assert len(expected_strategies) == 12, f"Expected 12 strategies from config, got {len(expected_strategies)}"

        available_strategies = set(m.get("strategy") for m in roi_results["metrics"] if isinstance(m, dict) and "strategy" in m)
        assert available_strategies.issubset(expected_strategies), f"Available strategies {available_strategies} not subset of expected {expected_strategies}"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        plots_created = {}

        # Benefit-cost ratios plot
        fig1 = self.plot_benefit_cost_ratios(roi_results, include_all_strategies=include_all_strategies)
        path1 = output_path / 'roi_benefit_cost_ratios.png'
        fig1.savefig(path1, dpi=300, bbox_inches='tight')
        plots_created['benefit_cost_ratios'] = str(path1)
        plt.close(fig1)

        # ROI percentages plot
        fig2 = self.plot_roi_percentages(roi_results, include_all_strategies=include_all_strategies)
        path2 = output_path / 'roi_percentages.png'
        fig2.savefig(path2, dpi=300, bbox_inches='tight')
        plots_created['roi_percentages'] = str(path2)
        plt.close(fig2)

        # Payback periods plot
        fig3 = self.plot_payback_periods(roi_results, include_all_strategies=include_all_strategies)
        path3 = output_path / 'roi_payback_periods.png'
        fig3.savefig(path3, dpi=300, bbox_inches='tight')
        plots_created['payback_periods'] = str(path3)
        plt.close(fig3)

        # Break-even probabilities plot
        fig4 = self.plot_break_even_probabilities(roi_results, include_all_strategies=include_all_strategies)
        path4 = output_path / 'roi_break_even_probabilities.png'
        fig4.savefig(path4, dpi=300, bbox_inches='tight')
        plots_created['break_even_probabilities'] = str(path4)
        plt.close(fig4)

        # Interactive dashboard
        dashboard = self.create_roi_dashboard(roi_results)
        dashboard_path = output_path / 'roi_dashboard.html'
        dashboard.write_html(str(dashboard_path))
        plots_created['interactive_dashboard'] = str(dashboard_path)

        return plots_created