"""
Cost-Minimization Analysis (CMA) Engine for V4 Health Economic Evaluation

This module provides cost-minimization analysis when clinical equivalence
has been established between treatment strategies.

Features:
- Equivalence testing with TOST methodology
- Cost minimization for equivalent strategies
- Bootstrap confidence interval estimation
- Sensitivity analysis
- Publication-quality results

Author: V4 Development Team
Date: October 2025
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from scipy import stats
from analysis.core.io import load_psa


from typing import Union



@dataclass
class CMAEquivalenceTest:
    """Results of equivalence testing for clinical outcomes."""
    strategy_a: str
    strategy_b: str
    effect_diff: float
    effect_diff_ci_lower: float
    effect_diff_ci_upper: float
    equivalence_margin: float
    equivalent: bool
    test_statistic: float
    p_value: float
    equivalence_bounds: Tuple[float, float]


@dataclass
class CMAResults:
    """Results from cost-minimization analysis."""
    base_case_results: pd.DataFrame
    equivalence_tests: List[CMAEquivalenceTest]
    cost_minimization_results: pd.DataFrame
    sensitivity_analysis: pd.DataFrame
    bootstrap_results: pd.DataFrame
    summary_stats: Dict[str, Any]
    recommendations: Dict[str, Any]

    def __post_init__(self):
        """Validate results structure."""
        required_cols = ['strategy', 'cost', 'effect', 'perspective']
        if not all(col in self.base_case_results.columns for col in required_cols):
            raise ValueError("base_case_results missing required columns")


class CostMinimizationEngine:
    """
    Cost-Minimization Analysis Engine.

    Performs CMA when treatments have equivalent clinical outcomes.
    Identifies the least costly treatment option among clinically equivalent alternatives.
    """

    def __init__(
        self,
        equivalence_margin: float = 0.01,
        bootstrap_samples: int = 1000,
        confidence_level: float = 0.95,
        random_seed: Optional[int] = None
    ):
        """Initialize CMA engine with parameters."""
        self.equivalence_margin = equivalence_margin
        self.bootstrap_samples = bootstrap_samples
        self.bootstrap_iterations = bootstrap_samples  # Alias for compatibility
        self.confidence_level = confidence_level
        self.random_seed = random_seed

        if random_seed is not None:
            np.random.seed(random_seed)

    def analyze(self, psa_data: pd.DataFrame) -> CMAResults:
        """
        Analyze PSA data for cost-minimization.

        Args:
            psa_data: DataFrame with PSA data

        Returns:
            CMAResults: CMA analysis results
        """
        # Add default perspective if missing
        if 'perspective' not in psa_data.columns:
            psa_data = psa_data.copy()
            psa_data['perspective'] = 'health_system'

        return self.run_analysis(psa_data)

    def sensitivity_analysis(self, psa_data: pd.DataFrame, margin_range: np.ndarray) -> pd.DataFrame:
        """
        Perform sensitivity analysis on equivalence margin.

        Args:
            psa_data: PSA data
            margin_range: Range of equivalence margins to test

        Returns:
            DataFrame with sensitivity results
        """
        results = []
        for margin in margin_range:
            tests = self._test_equivalence(psa_data, margin)
            equivalent_pairs = sum(1 for test in tests if test.equivalent)
            results.append({
                'parameter': 'equivalence_margin',
                'value': margin,
                'equivalent_pairs': equivalent_pairs
            })
        return pd.DataFrame(results)

    def run_analysis(
        self,
        psa_data: Union[str, Path, pd.DataFrame],
        strategies: Optional[List[str]] = None,
        perspective: str = "health_system",
        equivalence_margin: Optional[float] = None,
        **kwargs
    ) -> CMAResults:
        """
        Run cost-minimization analysis.

        Args:
            psa_data: Path to PSA data file or DataFrame
            strategies: List of strategies to analyze (default: all)
            perspective: Analysis perspective ('health_system' or 'societal')
            equivalence_margin: Equivalence margin for effect differences (default: 0.01)
            **kwargs: Additional analysis parameters

        Returns:
            CMAResults: Complete CMA analysis results
        """
        # Load and filter data
        if isinstance(psa_data, (str, Path)):
            data = load_psa(Path(psa_data))
        else:
            data = psa_data.copy()

        # Filter by perspective and strategies
        data = data[data['perspective'] == perspective]
        if strategies:
            data = data[data['strategy'].isin(strategies)]

        if data.empty:
            raise ValueError(f"No data found for perspective '{perspective}' and strategies {strategies}")

        # Set equivalence margin
        margin = equivalence_margin or self.equivalence_margin

        # Perform equivalence testing
        equivalence_tests = self._test_equivalence(data, margin)

        # Identify equivalent strategy pairs
        equivalent_pairs = [
            (test.strategy_a, test.strategy_b)
            for test in equivalence_tests
            if test.equivalent
        ]

        if not equivalent_pairs:
            # No equivalent strategy pairs found. CMA may not be appropriate (log not available)
            # Still proceed but note the limitation
            pass

        # Perform cost minimization
        cost_results = self._calculate_cost_minimization(data, equivalent_pairs)

        # Sensitivity analysis
        sensitivity_results = self._perform_sensitivity_analysis(data, equivalent_pairs, margin)

        # Bootstrap analysis
        bootstrap_results = self._bootstrap_analysis(data, equivalent_pairs, margin)

        # Generate summary statistics
        summary_stats = self._generate_summary_statistics(
            data, equivalence_tests, cost_results, bootstrap_results
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            cost_results, equivalence_tests, summary_stats
        )

        return CMAResults(
            base_case_results=data,
            equivalence_tests=equivalence_tests,
            cost_minimization_results=cost_results,
            sensitivity_analysis=sensitivity_results,
            bootstrap_results=bootstrap_results,
            summary_stats=summary_stats,
            recommendations=recommendations
        )

    def _test_equivalence(
        self,
        data: pd.DataFrame,
        equivalence_margin: float
    ) -> List[CMAEquivalenceTest]:
        """
        Test for equivalence between strategy pairs.

        Args:
            data: PSA data with strategy, cost, effect columns
            equivalence_margin: Equivalence margin for effect differences

        Returns:
            List of equivalence test results
        """
        strategies = data['strategy'].unique()
        equivalence_tests = []

        for i, strategy_a in enumerate(strategies):
            for strategy_b in strategies[i+1:]:
                # Extract effect data for both strategies
                effects_a = data[data['strategy'] == strategy_a]['effect']
                effects_b = data[data['strategy'] == strategy_b]['effect']

                # Calculate effect difference
                effect_diff = effects_a.mean() - effects_b.mean()

                # Calculate confidence interval
                se_diff = np.sqrt(effects_a.var()/len(effects_a) + effects_b.var()/len(effects_b))
                t_critical = stats.t.ppf((1 + self.confidence_level) / 2, len(effects_a) + len(effects_b) - 2)
                ci_lower = effect_diff - t_critical * se_diff
                ci_upper = effect_diff + t_critical * se_diff

                # Test equivalence (TOST - Two One-Sided Tests)
                # Equivalent if CI is within [-margin, +margin]
                equivalent = ci_lower >= -equivalence_margin and ci_upper <= equivalence_margin

                # Calculate test statistics
                t_stat = effect_diff / se_diff
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(effects_a) + len(effects_b) - 2))

                equivalence_bounds = (-equivalence_margin, equivalence_margin)

                test_result = CMAEquivalenceTest(
                    strategy_a=strategy_a,
                    strategy_b=strategy_b,
                    effect_diff=effect_diff,
                    effect_diff_ci_lower=ci_lower,
                    effect_diff_ci_upper=ci_upper,
                    equivalence_margin=equivalence_margin,
                    equivalent=equivalent,
                    test_statistic=t_stat,
                    p_value=p_value,
                    equivalence_bounds=equivalence_bounds
                )

                equivalence_tests.append(test_result)

        return equivalence_tests

    def _calculate_cost_minimization(
        self,
        data: pd.DataFrame,
        equivalent_pairs: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """
        Calculate cost minimization results.

        Args:
            data: PSA data
            equivalent_pairs: List of equivalent strategy pairs

        Returns:
            DataFrame with cost minimization results
        """
        results = []

        for strategy in data['strategy'].unique():
            strategy_data = data[data['strategy'] == strategy]

            # Calculate base case statistics
            cost_mean = strategy_data['cost'].mean()
            cost_ci_lower = strategy_data['cost'].quantile(0.025)
            cost_ci_upper = strategy_data['cost'].quantile(0.975)

            effect_mean = strategy_data['effect'].mean()
            effect_ci_lower = strategy_data['effect'].quantile(0.025)
            effect_ci_upper = strategy_data['effect'].quantile(0.975)

            # Find equivalent strategies and calculate cost savings
            equivalent_strategies = []
            max_cost_savings = 0
            min_cost_savings = 0

            for pair in equivalent_pairs:
                if strategy in pair:
                    other_strategy = pair[0] if pair[1] == strategy else pair[1]
                    other_cost = data[data['strategy'] == other_strategy]['cost'].mean()

                    if cost_mean < other_cost:
                        cost_savings = other_cost - cost_mean
                        max_cost_savings = max(max_cost_savings, cost_savings)
                    elif cost_mean > other_cost:
                        cost_savings = cost_mean - other_cost
                        min_cost_savings = max(min_cost_savings, cost_savings)

                    equivalent_strategies.append(other_strategy)

            results.append({
                'strategy': strategy,
                'cost_mean': cost_mean,
                'cost_ci_lower': cost_ci_lower,
                'cost_ci_upper': cost_ci_upper,
                'effect_mean': effect_mean,
                'effect_ci_lower': effect_ci_lower,
                'effect_ci_upper': effect_ci_upper,
                'equivalent_strategies': equivalent_strategies,
                'max_cost_savings': max_cost_savings,
                'min_cost_savings': min_cost_savings,
                'is_least_costly': max_cost_savings > 0
            })

        return pd.DataFrame(results)

    def _perform_sensitivity_analysis(
        self,
        data: pd.DataFrame,
        equivalent_pairs: List[Tuple[str, str]],
        equivalence_margin: float
    ) -> pd.DataFrame:
        """
        Perform sensitivity analysis on equivalence margin and cost differences.

        Args:
            data: PSA data
            equivalent_pairs: Equivalent strategy pairs
            equivalence_margin: Base equivalence margin

        Returns:
            DataFrame with sensitivity analysis results
        """
        sensitivity_results = []

        # Test different equivalence margins
        margins_to_test = [0.005, 0.01, 0.02, 0.05]  # 0.5%, 1%, 2%, 5%

        for margin in margins_to_test:
            tests = self._test_equivalence(data, margin)
            equivalent_count = sum(1 for test in tests if test.equivalent)

            sensitivity_results.append({
                'parameter': 'equivalence_margin',
                'value': margin,
                'equivalent_pairs': equivalent_count,
                'total_pairs': len(tests)
            })

        # Test impact of cost variability (if we had cost parameter uncertainty)
        # For now, just report the base case
        sensitivity_results.append({
            'parameter': 'base_case',
            'value': equivalence_margin,
            'equivalent_pairs': len(equivalent_pairs),
            'total_pairs': len(self._test_equivalence(data, equivalence_margin))
        })

        return pd.DataFrame(sensitivity_results)

    def _bootstrap_analysis(
        self,
        data: pd.DataFrame,
        equivalent_pairs: List[Tuple[str, str]],
        equivalence_margin: float
    ) -> pd.DataFrame:
        """
        Perform bootstrap analysis for confidence intervals.

        Args:
            data: PSA data
            equivalent_pairs: Equivalent strategy pairs
            equivalence_margin: Equivalence margin

        Returns:
            DataFrame with bootstrap results
        """
        bootstrap_results = []

        for strategy in data['strategy'].unique():
            strategy_data = data[data['strategy'] == strategy]

            # Bootstrap cost differences
            cost_bootstrap = []
            for _ in range(self.bootstrap_iterations):
                sample = strategy_data.sample(n=len(strategy_data), replace=True)
                cost_bootstrap.append(sample['cost'].mean())

            cost_ci_lower = np.percentile(cost_bootstrap, 2.5)
            cost_ci_upper = np.percentile(cost_bootstrap, 97.5)

            bootstrap_results.append({
                'strategy': strategy,
                'cost_bootstrap_mean': np.mean(cost_bootstrap),
                'cost_bootstrap_ci_lower': cost_ci_lower,
                'cost_bootstrap_ci_upper': cost_ci_upper,
                'cost_bootstrap_std': np.std(cost_bootstrap)
            })

        return pd.DataFrame(bootstrap_results)

    def _generate_summary_statistics(
        self,
        data: pd.DataFrame,
        equivalence_tests: List[CMAEquivalenceTest],
        cost_results: pd.DataFrame,
        bootstrap_results: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate summary statistics for CMA analysis."""
        equivalent_pairs = [test for test in equivalence_tests if test.equivalent]

        # Find least costly strategy among equivalent ones
        least_costly = cost_results.loc[cost_results['cost_mean'].idxmin()]

        return {
            'total_strategies': len(data['strategy'].unique()),
            'equivalent_pairs': len(equivalent_pairs),
            'total_possible_pairs': len(equivalence_tests),
            'equivalence_rate': len(equivalent_pairs) / len(equivalence_tests) if equivalence_tests else 0,
            'least_costly_strategy': least_costly['strategy'],
            'least_costly_mean': least_costly['cost_mean'],
            'max_cost_savings': cost_results['max_cost_savings'].max(),
            'analysis_type': 'cost_minimization',
            'equivalence_margin': self.equivalence_margin,
            'confidence_level': self.confidence_level
        }

    def _generate_recommendations(
        self,
        cost_results: pd.DataFrame,
        equivalence_tests: List[CMAEquivalenceTest],
        summary_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate recommendations based on CMA results."""
        least_costly = cost_results.loc[cost_results['cost_mean'].idxmin()]
        equivalent_pairs = [test for test in equivalence_tests if test.equivalent]

        recommendations = {
            'primary_recommendation': least_costly['strategy'],
            'rationale': f"Least costly strategy among {len(cost_results)} evaluated treatments",
            'cost_savings': least_costly['max_cost_savings'],
            'equivalence_established': len(equivalent_pairs) > 0,
            'confidence_level': self.confidence_level,
            'limitations': []
        }

        # Add limitations
        if len(equivalent_pairs) == 0:
            recommendations['limitations'].append(
                "No strategy pairs established clinical equivalence. CMA assumptions may not hold."
            )

        if least_costly['max_cost_savings'] < 100:  # Less than $100 savings
            recommendations['limitations'].append(
                "Cost savings are minimal. Consider other decision criteria."
            )

        return recommendations

    def save_results(
        self,
        results: CMAResults,
        output_dir: Union[str, Path],
        prefix: str = "cma"
    ) -> Dict[str, Path]:
        """
        Save CMA results to files.

        Args:
            results: CMA results to save
            output_dir: Output directory
            prefix: File prefix

        Returns:
            Dictionary of saved file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        # Save equivalence tests
        equiv_df = pd.DataFrame([
            {
                'strategy_a': test.strategy_a,
                'strategy_b': test.strategy_b,
                'effect_diff': test.effect_diff,
                'effect_diff_ci_lower': test.effect_diff_ci_lower,
                'effect_diff_ci_upper': test.effect_diff_ci_upper,
                'equivalence_margin': test.equivalence_margin,
                'equivalent': test.equivalent,
                'test_statistic': test.test_statistic,
                'p_value': test.p_value
            }
            for test in results.equivalence_tests
        ])

        equiv_file = output_dir / f"{prefix}_equivalence_tests.csv"
        equiv_df.to_csv(equiv_file, index=False)
        saved_files['equivalence_tests'] = equiv_file

        # Save cost minimization results
        cost_file = output_dir / f"{prefix}_cost_minimization.csv"
        results.cost_minimization_results.to_csv(cost_file, index=False)
        saved_files['cost_minimization'] = cost_file

        # Save sensitivity analysis
        sens_file = output_dir / f"{prefix}_sensitivity.csv"
        results.sensitivity_analysis.to_csv(sens_file, index=False)
        saved_files['sensitivity'] = sens_file

        # Save bootstrap results
        boot_file = output_dir / f"{prefix}_bootstrap.csv"
        results.bootstrap_results.to_csv(boot_file, index=False)
        saved_files['bootstrap'] = boot_file

        # Save summary
        summary_file = output_dir / f"{prefix}_summary.json"
        import json
        with open(summary_file, 'w') as f:
            json.dump(results.summary_stats, f, indent=2, default=str)
        saved_files['summary'] = summary_file

        return saved_files
