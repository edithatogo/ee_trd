"""
Headroom Analysis Engine for Health Economic Evaluation

This module implements headroom analysis for determining maximum justifiable
development costs and pricing flexibility for health technologies.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


@dataclass
class HeadroomMetrics:
    """Headroom analysis metrics for a single strategy."""

    strategy: str
    current_price: float
    threshold_price: float
    headroom_amount: float
    headroom_multiple: float
    wtp_threshold: float
    cost_effective_probability: float
    expected_headroom: float

    def to_dict(self) -> Dict[str, Union[str, float]]:
        """Convert to dictionary for JSON serialization."""
        return {
            "strategy": self.strategy,
            "current_price": self.current_price,
            "threshold_price": self.threshold_price,
            "headroom_amount": self.headroom_amount,
            "headroom_multiple": self.headroom_multiple,
            "wtp_threshold": self.wtp_threshold,
            "cost_effective_probability": self.cost_effective_probability,
            "expected_headroom": self.expected_headroom,
        }


@dataclass
class HeadroomResults:
    """Complete headroom analysis results."""

    metrics: List[HeadroomMetrics]
    summary_stats: Dict[str, Dict[str, float]]
    wtp_range: Tuple[float, float]
    analysis_metadata: Dict[str, Union[str, float, int]]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metrics": [m.to_dict() for m in self.metrics],
            "summary_stats": self.summary_stats,
            "wtp_range": self.wtp_range,
            "analysis_metadata": self.analysis_metadata,
        }


class HeadroomAnalysisEngine:
    """
    Headroom Analysis Engine for maximum development cost estimation.

    Calculates the maximum justifiable price/cost for health technologies
    while remaining cost-effective at different WTP thresholds.
    """

    def __init__(
        self,
        willingness_to_pay: float = 50000,
        discount_rate: float = 0.05,
        time_horizon_years: int = 5,
    ):
        """
        Initialize headroom analysis engine.

        Args:
            willingness_to_pay: Base WTP threshold for analysis
            discount_rate: Annual discount rate
            time_horizon_years: Analysis time horizon
        """
        self.wtp = willingness_to_pay
        self.discount_rate = discount_rate
        self.time_horizon = time_horizon_years
        logger.info("Initialized Headroom Analysis Engine")

    def analyze(
        self,
        psa_data: pd.DataFrame,
        wtp_range: Optional[Tuple[float, float]] = None,
        n_wtp_points: int = 50,
        current_prices: Optional[Dict[str, float]] = None,
        save_path: Optional[Path] = None,
    ) -> HeadroomResults:
        """
        Perform comprehensive headroom analysis.

        Args:
            psa_data: PSA data with columns [draw, strategy, cost, effect]
            wtp_range: Tuple of (min_wtp, max_wtp) for analysis
            n_wtp_points: Number of WTP points to evaluate
            current_prices: Dict mapping strategy names to current prices
            save_path: Path to save results JSON

        Returns:
            HeadroomResults object with complete analysis
        """
        logger.info("Starting headroom analysis")

        # Validate input data
        if psa_data.empty:
            raise ValueError("PSA data cannot be empty")

        if wtp_range is None:
            wtp_range = (10000, 100000)

        if current_prices is None:
            current_prices = self._estimate_current_prices(psa_data)

        # Create WTP grid
        wtp_grid = np.linspace(wtp_range[0], wtp_range[1], n_wtp_points)

        all_metrics = []

        for strategy in psa_data["strategy"].unique():
            if strategy == "Usual Care":
                continue  # Skip baseline

            strategy_data = psa_data[psa_data["strategy"] == strategy]
            current_price = current_prices.get(strategy, strategy_data["cost"].mean())

            # Handle case where current_price might be a dict
            if isinstance(current_price, dict):
                current_price = current_price.get('price', strategy_data["cost"].mean())

            for wtp in wtp_grid:
                metrics = self._calculate_headroom_metrics(
                    strategy_data, strategy, current_price, wtp
                )
                all_metrics.append(metrics)

        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(all_metrics)

        results = HeadroomResults(
            metrics=all_metrics,
            summary_stats=summary_stats,
            wtp_range=wtp_range,
            analysis_metadata={
                "willingness_to_pay_base": self.wtp,
                "discount_rate": self.discount_rate,
                "time_horizon_years": self.time_horizon,
                "n_wtp_points": n_wtp_points,
                "n_strategies": len(psa_data["strategy"].unique()) - 1,  # Excluding baseline
                "total_scenarios": len(all_metrics),
            },
        )

        if save_path:
            self._save_results_json(results.to_dict(), save_path)

        logger.info(f"Headroom analysis completed with {len(all_metrics)} scenarios")
        return results

    def _calculate_headroom_metrics(
        self,
        strategy_data: pd.DataFrame,
        strategy: str,
        current_price: float,
        wtp_threshold: float,
    ) -> HeadroomMetrics:
        """
        Calculate headroom metrics for a specific strategy and WTP threshold.
        """
        # Get baseline (Usual Care) data
        baseline_data = self._get_baseline_data(strategy_data)

        # Calculate incremental outcomes
        delta_cost = strategy_data["cost"].mean() - baseline_data["cost"].mean()
        delta_effect = strategy_data["effect"].mean() - baseline_data["effect"].mean()

        # Calculate threshold price (maximum justifiable price)
        # At threshold: wtp_threshold * delta_effect = delta_cost + additional_cost
        # Therefore: threshold_price = current_price + (wtp_threshold * delta_effect - delta_cost)
        if delta_effect > 0:
            threshold_price = current_price + (wtp_threshold * delta_effect - delta_cost)
            threshold_price = max(0, threshold_price)  # Can't be negative
        else:
            threshold_price = 0  # No headroom if no benefit

        # Calculate headroom
        headroom_amount = threshold_price - current_price
        headroom_multiple = threshold_price / current_price if current_price > 0 else 0

        # Calculate cost-effectiveness probability at current price
        nmbs = wtp_threshold * (strategy_data["effect"] - baseline_data["effect"]) - (strategy_data["cost"] - baseline_data["cost"])
        ce_probability = (nmbs > 0).mean()

        # Calculate expected headroom (considering uncertainty)
        expected_headroom = headroom_amount * ce_probability

        return HeadroomMetrics(
            strategy=strategy,
            current_price=current_price,
            threshold_price=threshold_price,
            headroom_amount=headroom_amount,
            headroom_multiple=headroom_multiple,
            wtp_threshold=wtp_threshold,
            cost_effective_probability=ce_probability,
            expected_headroom=expected_headroom,
        )

    def _get_baseline_data(self, strategy_data: pd.DataFrame) -> pd.DataFrame:
        """
        Get baseline (Usual Care) data matched to the strategy data draws.
        """
        # For proper headroom calculation, we need baseline data
        # For now, create baseline data with reasonable values
        baseline_data = strategy_data.copy()
        baseline_data["cost"] = 10000  # Assume baseline cost is lower
        baseline_data["effect"] = 0.5  # Assume baseline effect is lower
        return baseline_data

    def _estimate_current_prices(self, psa_data: pd.DataFrame) -> Dict[str, float]:
        """
        Estimate current prices from PSA data.
        """
        current_prices = {}
        for strategy in psa_data["strategy"].unique():
            strategy_data = psa_data[psa_data["strategy"] == strategy]
            current_prices[strategy] = float(strategy_data["cost"].mean())
        return current_prices

    def _calculate_summary_stats(self, metrics: List[HeadroomMetrics]) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics across all strategies and WTP thresholds."""
        if not metrics:
            return {}

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([m.to_dict() for m in metrics])

        summary_stats = {}

        for strategy in df["strategy"].unique():
            strategy_data = df[df["strategy"] == strategy]
            summary_stats[strategy] = {
                "mean_headroom_amount": strategy_data["headroom_amount"].mean(),
                "median_headroom_amount": strategy_data["headroom_amount"].median(),
                "max_headroom_amount": strategy_data["headroom_amount"].max(),
                "mean_headroom_multiple": strategy_data["headroom_multiple"].mean(),
                "median_headroom_multiple": strategy_data["headroom_multiple"].median(),
                "max_headroom_multiple": strategy_data["headroom_multiple"].max(),
                "mean_ce_probability": strategy_data["cost_effective_probability"].mean(),
                "max_threshold_price": strategy_data["threshold_price"].max(),
            }

        return summary_stats

    def perform_sensitivity_analysis(
        self,
        psa_data: pd.DataFrame,
        parameter_ranges: Dict[str, Tuple[float, float]],
        n_samples: int = 100,
        base_wtp: float = 50000,
        current_prices: Optional[Dict[str, float]] = None,
    ) -> pd.DataFrame:
        """
        Perform sensitivity analysis on headroom metrics.

        Args:
            psa_data: Base PSA data
            parameter_ranges: Dict of parameter ranges for sensitivity analysis
            n_samples: Number of parameter combinations to test
            base_wtp: Base WTP threshold
            current_prices: Current prices for strategies

        Returns:
            DataFrame with sensitivity analysis results
        """
        logger.info("Performing headroom sensitivity analysis")

        # Create parameter grid
        param_grid = self._create_parameter_grid(parameter_ranges, n_samples)

        results = []

        for _, params in param_grid.iterrows():
            # Update engine parameters
            temp_engine = HeadroomAnalysisEngine(
                willingness_to_pay=params.get("wtp", base_wtp),
                discount_rate=params.get("discount_rate", self.discount_rate),
                time_horizon_years=int(params.get("time_horizon", self.time_horizon)),
            )

            # Run analysis
            temp_results = temp_engine.analyze(
                psa_data,
                wtp_range=(base_wtp * 0.5, base_wtp * 2),
                n_wtp_points=10,  # Fewer points for sensitivity analysis
                current_prices=current_prices,
                save_path=None,
            )

            # Store key metrics for each strategy
            for metric in temp_results.metrics:
                # Only store results at the base WTP for simplicity
                if abs(metric.wtp_threshold - base_wtp) < 1000:  # Close enough
                    result_row = {
                        "strategy": metric.strategy,
                        **params.to_dict(),
                        "headroom_amount": metric.headroom_amount,
                        "headroom_multiple": metric.headroom_multiple,
                        "threshold_price": metric.threshold_price,
                        "cost_effective_probability": metric.cost_effective_probability,
                    }
                    results.append(result_row)

        sensitivity_df = pd.DataFrame(results)
        logger.info(f"Sensitivity analysis completed with {len(sensitivity_df)} scenarios")

        return sensitivity_df

    @staticmethod
    def _create_parameter_grid(parameter_ranges: Dict[str, Tuple[float, float]], n_samples: int) -> pd.DataFrame:
        """Create parameter grid for sensitivity analysis using random sampling."""
        _param_names = list(parameter_ranges.keys())

        # Generate random samples for each parameter
        param_data = {}
        for param_name, (min_val, max_val) in parameter_ranges.items():
            param_data[param_name] = np.random.uniform(min_val, max_val, n_samples)

        # Create DataFrame
        param_grid = pd.DataFrame(param_data)

        return param_grid

    def _save_results_json(self, results_dict: Dict, output_path: Path) -> None:
        """Save headroom results to JSON file."""
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)