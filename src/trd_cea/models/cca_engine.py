"""
Cost-Consequence Analysis (CCA) Engine for V4 Health Economic Evaluation

This module provides cost-consequence analysis where costs and outcomes
are presented separately without aggregation into a single metric.

Features:
- Disaggregated cost and outcome reporting
- Multiple outcome measures presentation
- Scenario analysis capabilities
- Publication-quality tabular outputs

Author: V4 Development Team
Date: October 2025
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

from trd_cea.core.io import load_psa


@dataclass
class CCAOutcomeMeasure:
    """Represents a single outcome measure in CCA."""
    name: str
    description: str
    unit: str
    higher_is_better: bool
    values: np.ndarray
    mean: float
    ci_lower: float
    ci_upper: float


@dataclass
class CCACostComponent:
    """Represents a cost component in CCA."""
    name: str
    description: str
    category: str  # e.g., 'direct_medical', 'productivity', 'societal'
    values: np.ndarray
    mean: float
    ci_lower: float
    ci_upper: float


@dataclass
class CCAResults:
    """Results from cost-consequence analysis."""
    base_case_results: pd.DataFrame
    strategies: List[str]
    cost_components: List[CCACostComponent]
    outcome_measures: List[CCAOutcomeMeasure]
    total_costs: Dict[str, Dict[str, float]]  # strategy -> {mean, ci_lower, ci_upper}
    summary_table: pd.DataFrame
    scenario_analysis: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate results structure."""
        required_cols = ['strategy', 'cost', 'effect', 'perspective']
        if not all(col in self.base_case_results.columns for col in required_cols):
            raise ValueError("base_case_results missing required columns")


class CostConsequenceEngine:
    """
    Cost-Consequence Analysis Engine.

    Presents costs and outcomes separately without aggregation.
    Useful when decision-makers want to see disaggregated results
    and apply their own weights to different outcomes.
    """

    def __init__(
        self,
        confidence_level: float = 0.95,
        random_seed: Optional[int] = None
    ):
        """Initialize CCA engine with parameters."""
        self.confidence_level = confidence_level
        self.random_seed = random_seed

        if random_seed is not None:
            np.random.seed(random_seed)

    def analyze(
        self,
        psa_data: pd.DataFrame,
        strategies: Optional[List[str]] = None,
        perspective: str = 'health_system',
        outcome_measures: Optional[List[str]] = None,
        cost_categories: Optional[List[str]] = None,
        **kwargs
    ) -> CCAResults:
        """
        Perform cost-consequence analysis.

        Args:
            psa_data: PSA data as DataFrame or path to file
            strategies: List of strategies to analyze (default: all)
            perspective: Analysis perspective ('health_system' or 'societal')
            outcome_measures: List of outcome measures to include
            cost_categories: Cost categories to break down
            **kwargs: Additional analysis parameters

        Returns:
            CCAResults: Complete CCA analysis results
        """
        # Load and filter data
        if isinstance(psa_data, (str, Path)):
            data = load_psa(psa_data)
        else:
            data = psa_data.copy()

        # Filter by perspective and strategies
        data = data[data['perspective'] == perspective]
        if strategies:
            data = data[data['strategy'].isin(strategies)]
            strategy_list = strategies
        else:
            strategy_list = sorted(data['strategy'].unique())

        if data.empty:
            raise ValueError(f"No data found for perspective '{perspective}' and strategies {strategies}")

        # Extract cost components (if available in data)
        cost_components = self._extract_cost_components(data, cost_categories)

        # Extract outcome measures
        outcome_measures_data = self._extract_outcome_measures(data, outcome_measures)

        # Calculate total costs per strategy
        total_costs = self._calculate_total_costs(data, strategy_list)

        # Create summary table
        summary_table = self._create_summary_table(
            data, strategy_list, outcome_measures_data, total_costs
        )

        # Scenario analysis (optional)
        scenario_results = self._perform_scenario_analysis(data, strategy_list)

        return CCAResults(
            base_case_results=data,
            strategies=strategy_list,
            cost_components=cost_components,
            outcome_measures=outcome_measures_data,
            total_costs=total_costs,
            summary_table=summary_table,
            scenario_analysis=scenario_results
        )

    def _extract_cost_components(
        self,
        data: pd.DataFrame,
        cost_categories: Optional[List[str]] = None
    ) -> List[CCACostComponent]:
        """Extract cost components from data."""
        components = []

        # If cost categories specified, try to extract them
        if cost_categories:
            for category in cost_categories:
                if f'cost_{category}' in data.columns:
                    values = data[f'cost_{category}'].values
                    components.append(CCACostComponent(
                        name=category,
                        description=f"{category.replace('_', ' ').title()} costs",
                        category=category,
                        values=values,
                        mean=np.mean(values),
                        ci_lower=np.percentile(values, (1 - self.confidence_level) / 2 * 100),
                        ci_upper=np.percentile(values, (1 + self.confidence_level) / 2 * 100)
                    ))

        # If no specific categories, use total cost
        if not components:
            total_costs = data.groupby('strategy')['cost'].apply(list)
            for strategy, costs in total_costs.items():
                values = np.array(costs)
                components.append(CCACostComponent(
                    name=f"total_cost_{strategy}",
                    description=f"Total costs for {strategy}",
                    category="total",
                    values=values,
                    mean=np.mean(values),
                    ci_lower=np.percentile(values, (1 - self.confidence_level) / 2 * 100),
                    ci_upper=np.percentile(values, (1 + self.confidence_level) / 2 * 100)
                ))

        return components

    def _extract_outcome_measures(
        self,
        data: pd.DataFrame,
        outcome_measures: Optional[List[str]] = None
    ) -> List[CCAOutcomeMeasure]:
        """Extract outcome measures from data."""
        measures = []

        # Default outcome measures
        default_measures = {
            'effect': {
                'description': 'Clinical effectiveness',
                'unit': 'QALYs',
                'higher_is_better': True
            }
        }

        measures_to_extract = outcome_measures or ['effect']

        for measure_name in measures_to_extract:
            if measure_name in data.columns:
                values = data[measure_name].values
                measure_info = default_measures.get(measure_name, {
                    'description': measure_name,
                    'unit': 'units',
                    'higher_is_better': True
                })

                measures.append(CCAOutcomeMeasure(
                    name=measure_name,
                    description=measure_info['description'],
                    unit=measure_info['unit'],
                    higher_is_better=measure_info['higher_is_better'],
                    values=values,
                    mean=np.mean(values),
                    ci_lower=np.percentile(values, (1 - self.confidence_level) / 2 * 100),
                    ci_upper=np.percentile(values, (1 + self.confidence_level) / 2 * 100)
                ))

        return measures

    def _calculate_total_costs(
        self,
        data: pd.DataFrame,
        strategies: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate total costs for each strategy."""
        total_costs = {}

        for strategy in strategies:
            strategy_data = data[data['strategy'] == strategy]['cost']
            if len(strategy_data) > 0:
                values = strategy_data.values
                total_costs[strategy] = {
                    'mean': np.mean(values),
                    'ci_lower': np.percentile(values, (1 - self.confidence_level) / 2 * 100),
                    'ci_upper': np.percentile(values, (1 + self.confidence_level) / 2 * 100),
                    'std': np.std(values)
                }
            else:
                total_costs[strategy] = {'mean': 0, 'ci_lower': 0, 'ci_upper': 0, 'std': 0}

        return total_costs

    def _create_summary_table(
        self,
        data: pd.DataFrame,
        strategies: List[str],
        outcome_measures: List[CCAOutcomeMeasure],
        total_costs: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        """Create summary table for CCA results."""
        summary_data = []

        for strategy in strategies:
            row = {'Strategy': strategy}

            # Add cost information
            if strategy in total_costs:
                cost_info = total_costs[strategy]
                row['Total Cost (Mean)'] = cost_info['mean']
                row['Total Cost (95% CI)'] = f"{cost_info['ci_lower']:.0f} - {cost_info['ci_upper']:.0f}"

            # Add outcome measures
            for measure in outcome_measures:
                strategy_mask = data['strategy'] == strategy
                if strategy_mask.any():
                    measure_values = data.loc[strategy_mask, measure.name].values
                    row[f'{measure.description} (Mean)'] = np.mean(measure_values)
                    ci_lower = np.percentile(measure_values, (1 - self.confidence_level) * 50)
                    ci_upper = np.percentile(measure_values, (1 + self.confidence_level) * 50)
                    row[f'{measure.description} (95% CI)'] = f"{ci_lower:.3f} - {ci_upper:.3f}"

            summary_data.append(row)

        return pd.DataFrame(summary_data)

    def _perform_scenario_analysis(
        self,
        data: pd.DataFrame,
        strategies: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Perform basic scenario analysis."""
        # Simple scenario: best/worst case for each strategy
        scenarios = {}

        for strategy in strategies:
            strategy_data = data[data['strategy'] == strategy]
            if not strategy_data.empty:
                scenarios[strategy] = {
                    'best_case': {
                        'cost': strategy_data['cost'].min(),
                        'effect': strategy_data['effect'].max()
                    },
                    'worst_case': {
                        'cost': strategy_data['cost'].max(),
                        'effect': strategy_data['effect'].min()
                    },
                    'base_case': {
                        'cost': strategy_data['cost'].mean(),
                        'effect': strategy_data['effect'].mean()
                    }
                }

        return scenarios if scenarios else None

    def save_results(self, results: CCAResults, output_path: str) -> None:
        """Save CCA results to file."""
        import json
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert results to dictionary
        results_dict = {
            'strategies': results.strategies,
            'total_costs': results.total_costs,
            'summary_table': results.summary_table.to_dict('records'),
            'cost_components': [
                {
                    'name': comp.name,
                    'description': comp.description,
                    'category': comp.category,
                    'mean': comp.mean,
                    'ci_lower': comp.ci_lower,
                    'ci_upper': comp.ci_upper
                }
                for comp in results.cost_components
            ],
            'outcome_measures': [
                {
                    'name': measure.name,
                    'description': measure.description,
                    'unit': measure.unit,
                    'higher_is_better': measure.higher_is_better,
                    'mean': measure.mean,
                    'ci_lower': measure.ci_lower,
                    'ci_upper': measure.ci_upper
                }
                for measure in results.outcome_measures
            ],
            'scenario_analysis': results.scenario_analysis,
            'metadata': {
                'analysis_type': 'cost_consequence_analysis',
                'confidence_level': self.confidence_level,
                'n_strategies': len(results.strategies)
            }
        }

        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)