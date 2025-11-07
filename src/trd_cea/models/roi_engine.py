"""
Return on Investment (ROI) Analysis Engine for Health Economic Evaluation

This module implements comprehensive ROI analysis for health technology assessment,
including benefit-cost ratios, payback period calculations, and sensitivity analysis.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


@dataclass
class ROIMetrics:
    """ROI analysis metrics for a single strategy."""

    strategy: str
    benefit_cost_ratio: float
    net_benefit: float
    payback_period_years: Optional[float]
    roi_percentage: float
    break_even_probability: float
    expected_value_of_roi: float

    def to_dict(self) -> Dict[str, Union[str, float]]:
        """Convert to dictionary for JSON serialization."""
        return {
            "strategy": self.strategy,
            "benefit_cost_ratio": self.benefit_cost_ratio,
            "net_benefit": self.net_benefit,
            "payback_period_years": self.payback_period_years,
            "roi_percentage": self.roi_percentage,
            "break_even_probability": self.break_even_probability,
            "expected_value_of_roi": self.expected_value_of_roi,
        }


@dataclass
class ROIResults:
    """Complete ROI analysis results."""

    metrics: List[ROIMetrics]
    summary_stats: Dict[str, Dict[str, float]]
    psa_data: pd.DataFrame
    analysis_metadata: Dict[str, Union[str, float, int]]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metrics": [metric.to_dict() for metric in self.metrics],
            "summary_stats": self.summary_stats,
            "psa_data_shape": self.psa_data.shape,
            "analysis_metadata": self.analysis_metadata,
        }


class ROIAnalysisEngine:
    """
    Return on Investment Analysis Engine for Health Economic Evaluation.

    This engine calculates comprehensive ROI metrics including:
    - Benefit-cost ratios
    - Payback period analysis
    - ROI percentages
    - Break-even probability
    - Expected value of ROI
    """

    def __init__(
        self,
        willingness_to_pay: float = 50000,
        discount_rate: float = 0.05,
        time_horizon_years: int = 5,
    ):
        """
        Initialize ROI analysis engine.

        Args:
            willingness_to_pay: WTP threshold in currency units per QALY
            discount_rate: Annual discount rate for future benefits/costs
            time_horizon_years: Analysis time horizon in years
        """
        self.wtp = willingness_to_pay
        self.discount_rate = discount_rate
        self.time_horizon = time_horizon_years

        logger.info(
            f"Initialized ROI engine with WTP=${self.wtp:,.0f}, "
            f"discount_rate={self.discount_rate:.1%}, "
            f"time_horizon={self.time_horizon} years"
        )

    def analyze(
        self,
        psa_data: pd.DataFrame,
        strategies: Optional[List[str]] = None,
        save_path: Optional[Path] = None,
    ) -> ROIResults:
        """
        Perform comprehensive ROI analysis.

        Args:
            psa_data: PSA data with columns [draw, strategy, cost, effect]
            strategies: List of strategies to analyze (default: all)
            save_path: Optional path to save results JSON

        Returns:
            ROIResults object with complete analysis
        """
        logger.info("Starting ROI analysis")

        # Validate input data
        self._validate_psa_data(psa_data)

        # Filter strategies if specified
        if strategies:
            psa_data = psa_data[psa_data["strategy"].isin(strategies)].copy()
            logger.info(f"Filtered to {len(strategies)} strategies: {strategies}")

        # Calculate ROI metrics for each strategy
        metrics = []
        for strategy in psa_data["strategy"].unique():
            strategy_data = psa_data[psa_data["strategy"] == strategy]
            roi_metric = self._calculate_roi_metrics(strategy_data, strategy)
            metrics.append(roi_metric)

        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(metrics)

        # Create results object
        results = ROIResults(
            metrics=metrics,
            summary_stats=summary_stats,
            psa_data=psa_data,
            analysis_metadata={
                "willingness_to_pay": self.wtp,
                "discount_rate": self.discount_rate,
                "time_horizon_years": self.time_horizon,
                "n_strategies": len(metrics),
                "n_psa_draws": len(psa_data["draw"].unique()),
                "analysis_type": "roi_analysis",
            },
        )

        # Save results if path provided
        if save_path:
            try:
                self._save_results_json(results.to_dict(), save_path)
                logger.info(f"Results saved to {save_path}")
            except Exception as e:
                logger.error(f"Failed to save results to {save_path}: {e}")
                # Continue execution even if save fails

        logger.info("ROI analysis completed")
        return results

    def _validate_psa_data(self, psa_data: pd.DataFrame) -> None:
        """Validate PSA data structure and content."""
        required_cols = ["draw", "strategy", "cost", "effect"]
        missing_cols = [col for col in required_cols if col not in psa_data.columns]

        if missing_cols:
            raise ValueError(f"PSA data missing required columns: {missing_cols}")

        if psa_data.empty:
            raise ValueError("PSA data is empty")

        # Check for negative costs or effects
        if (psa_data["cost"] < 0).any():
            logger.warning("Negative costs found in PSA data")
        if (psa_data["effect"] < 0).any():
            logger.warning("Negative effects found in PSA data")

    def _calculate_roi_metrics(
        self, strategy_data: pd.DataFrame, strategy: str
    ) -> ROIMetrics:
        """Calculate ROI metrics for a single strategy."""
        # Calculate net monetary benefit for each draw: NMB = λ × Effect - Cost
        nmbs = self.wtp * strategy_data["effect"] - strategy_data["cost"]

        # Calculate benefit-cost ratio (benefits/costs)
        total_benefits = strategy_data["effect"] * self.wtp
        total_costs = strategy_data["cost"]
        benefit_cost_ratios = total_benefits / total_costs.replace(0, np.nan)

        # Handle division by zero and negative ratios
        benefit_cost_ratios = benefit_cost_ratios.fillna(0)
        benefit_cost_ratios = benefit_cost_ratios.clip(lower=0)

        # Calculate payback period (when cumulative NMB becomes positive)
        payback_period = self._calculate_payback_period(strategy_data)

        # Calculate ROI percentage
        avg_benefits = total_benefits.mean()
        avg_costs = total_costs.mean()
        if avg_benefits == 0:
            roi_percentage = 0  # No benefits means no return
        elif avg_costs > 0:
            roi_percentage = ((avg_benefits - avg_costs) / avg_costs) * 100
        else:
            roi_percentage = 0

        # Calculate break-even probability (probability NMB > 0)
        break_even_prob = (nmbs > 0).mean()

        # Calculate expected value of ROI
        ev_roi = nmbs.mean()

        return ROIMetrics(
            strategy=strategy,
            benefit_cost_ratio=benefit_cost_ratios.mean(),
            net_benefit=nmbs.mean(),
            payback_period_years=payback_period,
            roi_percentage=roi_percentage,
            break_even_probability=break_even_prob,
            expected_value_of_roi=ev_roi,
        )

    def _calculate_payback_period(self, strategy_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate payback period in years.

        This is a simplified calculation assuming uniform cash flows.
        In a real implementation, this would use detailed cash flow projections.
        """
        # For this simplified version, assume costs are incurred upfront
        # and benefits accrue over the time horizon
        avg_cost = strategy_data["cost"].mean()
        avg_benefit = strategy_data["effect"].mean() * self.wtp

        if avg_benefit <= 0 or avg_cost <= 0:
            return None  # No payback if no benefits or no costs

        # Simple payback period assuming linear benefit accrual
        annual_benefit = avg_cost / avg_benefit
        payback_years = avg_cost / annual_benefit

        # Cap at time horizon
        return min(payback_years, self.time_horizon)

    def _calculate_summary_stats(self, metrics: List[ROIMetrics]) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics across all strategies."""
        if not metrics:
            return {}

        # Extract values for statistical analysis
        benefit_cost_ratios = [m.benefit_cost_ratio for m in metrics]
        net_benefits = [m.net_benefit for m in metrics]
        roi_percentages = [m.roi_percentage for m in metrics]
        break_even_probs = [m.break_even_probability for m in metrics]

        return {
            "benefit_cost_ratio": {
                "mean": np.mean(benefit_cost_ratios),
                "std": np.std(benefit_cost_ratios),
                "min": np.min(benefit_cost_ratios),
                "max": np.max(benefit_cost_ratios),
            },
            "net_benefit": {
                "mean": np.mean(net_benefits),
                "std": np.std(net_benefits),
                "min": np.min(net_benefits),
                "max": np.max(net_benefits),
            },
            "roi_percentage": {
                "mean": np.mean(roi_percentages),
                "std": np.std(roi_percentages),
                "min": np.min(roi_percentages),
                "max": np.max(roi_percentages),
            },
            "break_even_probability": {
                "mean": np.mean(break_even_probs),
                "std": np.std(break_even_probs),
                "min": np.min(break_even_probs),
                "max": np.max(break_even_probs),
            },
        }

    def perform_sensitivity_analysis(
        self,
        psa_data: pd.DataFrame,
        parameter_ranges: Dict[str, Tuple[float, float]],
        n_samples: int = 1000,
    ) -> pd.DataFrame:
        """
        Perform sensitivity analysis on ROI metrics.

        Args:
            psa_data: Base PSA data
            parameter_ranges: Dict of parameter ranges for sensitivity analysis
            n_samples: Number of parameter combinations to test

        Returns:
            DataFrame with sensitivity analysis results
        """
        logger.info("Performing ROI sensitivity analysis")

        # Create parameter grid
        param_grid = self._create_parameter_grid(parameter_ranges, n_samples)

        results = []

        for _, params in param_grid.iterrows():
            # Update engine parameters
            temp_engine = ROIAnalysisEngine(
                willingness_to_pay=params.get("wtp", self.wtp),
                discount_rate=params.get("discount_rate", self.discount_rate),
                time_horizon_years=int(params.get("time_horizon", self.time_horizon)),
            )

            # Run analysis
            temp_results = temp_engine.analyze(psa_data, save_path=None)

            # Store key metrics
            for metric in temp_results.metrics:
                result_row = {
                    "strategy": metric.strategy,
                    **params.to_dict(),
                    "benefit_cost_ratio": metric.benefit_cost_ratio,
                    "net_benefit": metric.net_benefit,
                    "roi_percentage": metric.roi_percentage,
                    "break_even_probability": metric.break_even_probability,
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
        """Save ROI results to JSON file."""
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)