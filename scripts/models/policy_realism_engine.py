"""
Policy Realism Toggles for V4 Health Economic Analysis

This module provides country-specific and jurisdiction-specific policy parameter
toggles to enable realistic implementation scenarios and sensitivity analysis.

Features:
- Country-specific reimbursement policies
- Jurisdiction-specific implementation constraints
- Policy scenario sensitivity analysis
- Integration with existing analysis engines

Author: V4 Development Team
Date: October 2025
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import logging

from analysis.core.io import save_results

# Configure logger for this module
logger = logging.getLogger(__name__)


@dataclass
class PolicyScenario:
    """Configuration for a specific policy scenario."""

    name: str
    description: str
    jurisdiction: str  # 'AU', 'NZ', or 'both'
    perspective: str  # 'health_system' or 'societal'

    # Reimbursement policies
    reimbursement_rates: Dict[str, float] = field(default_factory=dict)
    coverage_restrictions: Dict[str, Any] = field(default_factory=dict)
    prior_authorization_requirements: Dict[str, bool] = field(default_factory=dict)

    # Implementation constraints
    staffing_requirements: Dict[str, Any] = field(default_factory=dict)
    facility_requirements: Dict[str, Any] = field(default_factory=dict)
    training_mandates: Dict[str, Any] = field(default_factory=dict)

    # Cost implications
    administrative_burden: Dict[str, float] = field(default_factory=dict)
    monitoring_costs: Dict[str, float] = field(default_factory=dict)
    compliance_costs: Dict[str, float] = field(default_factory=dict)

    # Access and equity considerations
    eligibility_criteria: Dict[str, Any] = field(default_factory=dict)
    regional_variations: Dict[str, Any] = field(default_factory=dict)
    indigenous_access_provisions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyToggleResults:
    """Results from applying policy toggles to analysis."""

    base_case_results: pd.DataFrame
    policy_scenario_results: Dict[str, pd.DataFrame]
    sensitivity_analysis: pd.DataFrame
    implementation_impact: pd.DataFrame

    # Summary metrics
    policy_summary: Dict[str, Any]


class PolicyRealismEngine:
    """
    Engine for applying policy realism toggles to health economic analysis.

    Provides country-specific and jurisdiction-specific policy configurations
    to enable realistic implementation scenarios and sensitivity analysis.
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the policy realism engine.

        Args:
            config_path: Path to policy configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.policy_scenarios = {}
        self._load_default_scenarios()

        if self.config_path and self.config_path.exists():
            self._load_custom_scenarios()

    def _load_default_scenarios(self):
        """Load default policy scenarios for AU and NZ."""
        logger.info("Loading default policy scenarios...")

        # Australian policy scenarios
        self.policy_scenarios.update({
            "au_conservative": PolicyScenario(
                name="au_conservative",
                description="Conservative Australian reimbursement - limited coverage, high barriers",
                jurisdiction="AU",
                perspective="health_system",
                reimbursement_rates={
                    "ECT": 0.46,  # 46% of costs reimbursed
                    "IV-KA": 0.6,  # 60% - experimental therapy
                    "KA-ECT": 0.5,  # 50% - novel combination
                    "rTMS": 0.8,   # 80% - established
                    "Usual Care": 1.0  # 100% - standard care
                },
                coverage_restrictions={
                    "IV-KA": {"max_sessions": 6, "requires_specialist": True},
                    "KA-ECT": {"requires_anaesthetist": True, "hospital_only": True},
                    "rTMS": {"max_sessions": 30, "requires_neurologist": True}
                },
                prior_authorization_requirements={
                    "IV-KA": True,
                    "KA-ECT": True,
                    "rTMS": True,
                    "ECT": False  # Established therapy
                },
                staffing_requirements={
                    "IV-KA": {"psychiatrists": 1, "nurses": 2, "anaesthetists": 1},
                    "KA-ECT": {"psychiatrists": 1, "nurses": 3, "anaesthetists": 2},
                    "ECT": {"psychiatrists": 1, "nurses": 2}
                },
                administrative_burden={
                    "IV-KA": 0.15,  # 15% administrative overhead
                    "KA-ECT": 0.20,  # 20% administrative overhead
                    "rTMS": 0.10    # 10% administrative overhead
                },
                eligibility_criteria={
                    "treatment_resistant": True,
                    "minimum_episodes": 2,
                    "max_age": 75
                }
            ),

            "au_progressive": PolicyScenario(
                name="au_progressive",
                description="Progressive Australian reimbursement - expanded access, lower barriers",
                jurisdiction="AU",
                perspective="health_system",
                reimbursement_rates={
                    "ECT": 1.0,
                    "IV-KA": 0.8,
                    "KA-ECT": 0.75,
                    "rTMS": 0.9,
                    "Usual Care": 1.0
                },
                coverage_restrictions={
                    "IV-KA": {"max_sessions": 12, "can_be_outpatient": True},
                    "KA-ECT": {"can_be_outpatient": True},
                    "rTMS": {"max_sessions": 60}
                },
                prior_authorization_requirements={
                    "IV-KA": False,  # Streamlined approval
                    "KA-ECT": True,
                    "rTMS": False
                },
                administrative_burden={
                    "IV-KA": 0.08,  # Reduced administrative burden
                    "KA-ECT": 0.12,
                    "rTMS": 0.05
                },
                regional_variations={
                    "rural_access": {"additional_reimbursement": 0.1},
                    "telemedicine": {"allowed": True, "reimbursement_rate": 0.8}
                }
            )
        })

        # New Zealand policy scenarios
        self.policy_scenarios.update({
            "nz_universal": PolicyScenario(
                name="nz_universal",
                description="New Zealand universal coverage - comprehensive access",
                jurisdiction="NZ",
                perspective="health_system",
                reimbursement_rates={
                    "ECT": 1.0,
                    "IV-KA": 0.9,
                    "KA-ECT": 0.85,
                    "rTMS": 0.95,
                    "Usual Care": 1.0
                },
                coverage_restrictions={},  # Minimal restrictions
                prior_authorization_requirements={
                    "KA-ECT": True,  # Only for complex procedures
                },
                regional_variations={
                    "district_health_boards": {"equal_access": True},
                    "maori_health": {"cultural_competence_required": True}
                },
                indigenous_access_provisions={
                    "maori": {"cultural_adaptation_required": True, "additional_funding": 0.1},
                    "pacific": {"community_engagement_required": True}
                }
            ),

            "nz_conservative": PolicyScenario(
                name="nz_conservative",
                description="Conservative New Zealand reimbursement - cost containment focus",
                jurisdiction="NZ",
                perspective="health_system",
                reimbursement_rates={
                    "ECT": 0.85,
                    "IV-KA": 0.5,
                    "KA-ECT": 0.4,
                    "rTMS": 0.7,
                    "Usual Care": 1.0
                },
                coverage_restrictions={
                    "IV-KA": {"requires_cost_benefit_analysis": True},
                    "KA-ECT": {"requires_ethics_approval": True}
                },
                prior_authorization_requirements={
                    "IV-KA": True,
                    "KA-ECT": True,
                    "rTMS": True
                },
                administrative_burden={
                    "IV-KA": 0.25,  # High administrative burden
                    "KA-ECT": 0.30,
                    "rTMS": 0.15
                }
            )
        })

        # Cross-jurisdictional scenarios
        self.policy_scenarios.update({
            "harmonized_access": PolicyScenario(
                name="harmonized_access",
                description="Harmonized access across AU/NZ - reduced cross-border barriers",
                jurisdiction="both",
                perspective="health_system",
                reimbursement_rates={
                    "ECT": 0.95,
                    "IV-KA": 0.75,
                    "KA-ECT": 0.7,
                    "rTMS": 0.85,
                    "Usual Care": 1.0
                },
                regional_variations={
                    "cross_border_access": {"allowed": True, "reimbursement_rate": 0.8},
                    "telemedicine": {"international_allowed": True}
                }
            )
        })

    def _load_custom_scenarios(self):
        """Load custom policy scenarios from configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                custom_config = yaml.safe_load(f)

            for scenario_name, scenario_data in custom_config.get('policy_scenarios', {}).items():
                scenario = PolicyScenario(**scenario_data)
                self.policy_scenarios[scenario_name] = scenario

            logger.info(f"Loaded {len(custom_config.get('policy_scenarios', {}))} custom policy scenarios")

        except Exception as e:
            logger.warning(f"Could not load custom scenarios: {e}")

    def apply_policy_toggles(
        self,
        base_results: pd.DataFrame,
        scenario_names: List[str],
        jurisdiction: str = "AU",
        perspective: str = "health_system"
    ) -> PolicyToggleResults:
        """
        Apply policy toggles to analysis results.

        Args:
            base_results: Base case analysis results
            scenario_names: List of policy scenario names to apply
            jurisdiction: Jurisdiction ('AU', 'NZ', or 'both')
            perspective: Perspective ('health_system' or 'societal')

        Returns:
            PolicyToggleResults with modified results for each scenario
        """
        logger.info(f"Applying policy toggles for {jurisdiction} ({perspective} perspective)")

        # Filter scenarios by jurisdiction and perspective
        applicable_scenarios = {
            name: scenario for name, scenario in self.policy_scenarios.items()
            if (scenario.jurisdiction == jurisdiction or scenario.jurisdiction == "both") and
               scenario.perspective == perspective
        }

        # Only apply requested scenarios
        scenarios_to_apply = {name: applicable_scenarios[name] for name in scenario_names
                            if name in applicable_scenarios}

        if not scenarios_to_apply:
            logger.warning("No applicable policy scenarios found")
            return PolicyToggleResults(
                base_case_results=base_results,
                policy_scenario_results={},
                sensitivity_analysis=pd.DataFrame(),
                implementation_impact=pd.DataFrame(),
                policy_summary={"warning": "No applicable scenarios"}
            )

        # Apply each policy scenario
        policy_results = {}
        sensitivity_data = []
        implementation_impacts = []

        for scenario_name, scenario in scenarios_to_apply.items():
            logger.info(f"Applying scenario: {scenario_name}")

            modified_results = self._apply_single_policy_scenario(
                base_results.copy(), scenario
            )
            policy_results[scenario_name] = modified_results

            # Calculate sensitivity metrics
            sensitivity_data.extend(self._calculate_sensitivity_metrics(
                base_results, modified_results, scenario_name
            ))

            # Calculate implementation impact
            implementation_impacts.extend(self._calculate_implementation_impact(
                base_results, modified_results, scenario
            ))

        # Create summary
        policy_summary = self._create_policy_summary(
            base_results, policy_results, scenarios_to_apply
        )

        return PolicyToggleResults(
            base_case_results=base_results,
            policy_scenario_results=policy_results,
            sensitivity_analysis=pd.DataFrame(sensitivity_data),
            implementation_impact=pd.DataFrame(implementation_impacts),
            policy_summary=policy_summary
        )

    def _apply_single_policy_scenario(
        self,
        results: pd.DataFrame,
        scenario: PolicyScenario
    ) -> pd.DataFrame:
        """
        Apply a single policy scenario to results.

        Args:
            results: Analysis results DataFrame
            scenario: Policy scenario to apply

        Returns:
            Modified results DataFrame
        """
        modified_results = results.copy()

        # Apply reimbursement rate adjustments
        if 'strategy' in modified_results.columns and 'cost' in modified_results.columns:
            for strategy in modified_results['strategy'].unique():
                if strategy in scenario.reimbursement_rates:
                    rate = scenario.reimbursement_rates[strategy]
                    mask = modified_results['strategy'] == strategy
                    modified_results.loc[mask, 'cost'] *= rate

        # Apply administrative burden
        if 'strategy' in modified_results.columns and 'cost' in modified_results.columns:
            for strategy in modified_results['strategy'].unique():
                burden = scenario.administrative_burden.get(strategy, 0.15)
                mask = modified_results['strategy'] == strategy
                modified_results.loc[mask, 'cost'] *= (1 + burden)

        # Add policy scenario identifier
        modified_results['policy_scenario'] = scenario.name

        return modified_results

    def _calculate_sensitivity_metrics(
        self,
        base_results: pd.DataFrame,
        modified_results: pd.DataFrame,
        scenario_name: str
    ) -> List[Dict[str, Any]]:
        """
        Calculate sensitivity metrics for policy scenario.

        Args:
            base_results: Original results
            modified_results: Modified results
            scenario_name: Name of policy scenario

        Returns:
            List of sensitivity metric dictionaries
        """
        sensitivity_data = []

        # Calculate key metrics for each strategy
        for strategy in base_results['strategy'].unique():
            base_strategy = base_results[base_results['strategy'] == strategy]
            modified_strategy = modified_results[modified_results['strategy'] == strategy]

            if len(base_strategy) > 0 and len(modified_strategy) > 0:
                base_cost = base_strategy['cost'].mean()
                base_effect = base_strategy['effect'].mean()
                modified_cost = modified_strategy['cost'].mean()
                modified_effect = modified_strategy['effect'].mean()

                sensitivity_data.append({
                    'scenario': scenario_name,
                    'strategy': strategy,
                    'base_cost': base_cost,
                    'modified_cost': modified_cost,
                    'cost_change_percent': ((modified_cost - base_cost) / base_cost) * 100,
                    'base_effect': base_effect,
                    'modified_effect': modified_effect,
                    'effect_change_percent': ((modified_effect - base_effect) / base_effect) * 100 if base_effect != 0 else 0,
                    'icer_change': self._calculate_icer_change(base_strategy, modified_strategy)
                })

        return sensitivity_data

    def _calculate_icer_change(
        self,
        base_strategy: pd.DataFrame,
        modified_strategy: pd.DataFrame
    ) -> float:
        """
        Calculate change in ICER due to policy scenario.

        Args:
            base_strategy: Base case results for strategy
            modified_strategy: Modified results for strategy

        Returns:
            ICER change percentage
        """
        # Simplified ICER calculation (would be more sophisticated in practice)
        try:
            base_cost_diff = base_strategy['cost'].mean()
            base_effect_diff = base_strategy['effect'].mean()
            modified_cost_diff = modified_strategy['cost'].mean()
            modified_effect_diff = modified_strategy['effect'].mean()

            base_icer = base_cost_diff / base_effect_diff if base_effect_diff != 0 else float('inf')
            modified_icer = modified_cost_diff / modified_effect_diff if modified_effect_diff != 0 else float('inf')

            if base_icer == float('inf') or modified_icer == float('inf'):
                return 0.0

            return ((modified_icer - base_icer) / base_icer) * 100
        except Exception:
            return 0.0

    def _calculate_implementation_impact(
        self,
        base_results: pd.DataFrame,
        modified_results: pd.DataFrame,
        scenario: PolicyScenario
    ) -> List[Dict[str, Any]]:
        """
        Calculate implementation impact of policy scenario.

        Args:
            base_results: Original results
            modified_results: Modified results
            scenario: Policy scenario

        Returns:
            List of implementation impact dictionaries
        """
        implementation_data = []

        for strategy in base_results['strategy'].unique():
            base_cost = base_results[base_results['strategy'] == strategy]['cost'].mean()
            modified_cost = modified_results[modified_results['strategy'] == strategy]['cost'].mean()

            implementation_data.append({
                'scenario': scenario.name,
                'strategy': strategy,
                'reimbursement_rate': scenario.reimbursement_rates.get(strategy, 1.0),
                'administrative_burden': scenario.administrative_burden.get(strategy, 0.0),
                'requires_prior_auth': scenario.prior_authorization_requirements.get(strategy, False),
                'cost_impact': modified_cost - base_cost,
                'cost_impact_percent': ((modified_cost - base_cost) / base_cost) * 100 if base_cost != 0 else 0,
                'implementation_complexity': self._assess_implementation_complexity(scenario, strategy)
            })

        return implementation_data

    def _assess_implementation_complexity(
        self,
        scenario: PolicyScenario,
        strategy: str
    ) -> str:
        """
        Assess implementation complexity for a strategy under a policy scenario.

        Args:
            scenario: Policy scenario
            strategy: Treatment strategy

        Returns:
            Complexity assessment string
        """
        complexity_score = 0

        # Prior authorization increases complexity
        if scenario.prior_authorization_requirements.get(strategy, False):
            complexity_score += 2

        # Administrative burden increases complexity
        burden = scenario.administrative_burden.get(strategy, 0.0)
        complexity_score += burden * 10  # Scale burden to score

        # Coverage restrictions increase complexity
        if strategy in scenario.coverage_restrictions:
            complexity_score += 1

        # Staffing requirements increase complexity
        if strategy in scenario.staffing_requirements:
            staff_count = sum(scenario.staffing_requirements[strategy].values())
            complexity_score += staff_count * 0.5

        if complexity_score < 2:
            return "Low"
        elif complexity_score < 5:
            return "Medium"
        else:
            return "High"

    def _create_policy_summary(
        self,
        base_results: pd.DataFrame,
        policy_results: Dict[str, pd.DataFrame],
        scenarios: Dict[str, PolicyScenario]
    ) -> Dict[str, Any]:
        """
        Create comprehensive policy summary.

        Args:
            base_results: Base case results
            policy_results: Results for each policy scenario
            scenarios: Policy scenario configurations

        Returns:
            Dictionary with policy summary
        """
        summary = {
            'total_scenarios_applied': len(policy_results),
            'scenarios': list(scenarios.keys()),
            'jurisdiction': list(scenarios.values())[0].jurisdiction if scenarios else None,
            'perspective': list(scenarios.values())[0].perspective if scenarios else None,
            'key_findings': []
        }

        # Calculate overall impact
        base_total_cost = base_results['cost'].sum()
        max_cost_impact = 0
        max_cost_scenario = None

        for scenario_name, results in policy_results.items():
            scenario_cost = results['cost'].sum()
            cost_impact = ((scenario_cost - base_total_cost) / base_total_cost) * 100

            if abs(cost_impact) > abs(max_cost_impact):
                max_cost_impact = cost_impact
                max_cost_scenario = scenario_name

        summary['max_cost_impact_percent'] = max_cost_impact
        summary['max_cost_impact_scenario'] = max_cost_scenario

        # Key findings
        if max_cost_impact > 10:
            summary['key_findings'].append("Significant cost impact from policy changes")
        elif max_cost_impact < -10:
            summary['key_findings'].append("Policy changes substantially reduce costs")
        else:
            summary['key_findings'].append("Moderate policy impact on costs")

        # Implementation complexity assessment
        high_complexity_scenarios = [
            name for name, scenario in scenarios.items()
            if any(self._assess_implementation_complexity(scenario, strategy) == "High"
                  for strategy in ['IV-KA', 'KA-ECT', 'rTMS'])
        ]

        if high_complexity_scenarios:
            summary['key_findings'].append(
                f"High implementation complexity in scenarios: {', '.join(high_complexity_scenarios)}"
            )

        return summary

    def save_policy_results(
        self,
        results: PolicyToggleResults,
        output_dir: str = "results/policy_analysis"
    ) -> None:
        """
        Save policy toggle results to disk.

        Args:
            results: Policy toggle results to save
            output_dir: Output directory
        """
        logger.info(f"Saving policy analysis results to {output_dir}")

        # Save base case results
        save_results(results.base_case_results, Path(f"{output_dir}/base_case_results.csv"))

        # Save policy scenario results
        for scenario_name, scenario_results in results.policy_scenario_results.items():
            save_results(scenario_results, Path(f"{output_dir}/{scenario_name}_results.csv"))

        # Save sensitivity analysis
        save_results(results.sensitivity_analysis, Path(f"{output_dir}/sensitivity_analysis.csv"))

        # Save implementation impact
        save_results(results.implementation_impact, Path(f"{output_dir}/implementation_impact.csv"))

        # Save policy summary
        summary_df = pd.DataFrame(list(results.policy_summary.items()), columns=["metric", "value"])
        save_results(summary_df, Path(f"{output_dir}/policy_summary.csv"))

        logger.info("Policy analysis results saved successfully")

    def get_available_scenarios(
        self,
        jurisdiction: Optional[str] = None,
        perspective: Optional[str] = None
    ) -> List[str]:
        """
        Get list of available policy scenarios.

        Args:
            jurisdiction: Filter by jurisdiction ('AU', 'NZ', or 'both')
            perspective: Filter by perspective ('health_system' or 'societal')

        Returns:
            List of scenario names
        """
        scenarios = self.policy_scenarios.keys()

        if jurisdiction:
            scenarios = [s for s in scenarios
                        if self.policy_scenarios[s].jurisdiction == jurisdiction or
                           self.policy_scenarios[s].jurisdiction == "both"]

        if perspective:
            scenarios = [s for s in scenarios
                        if self.policy_scenarios[s].perspective == perspective]

        return list(scenarios)

    def get_scenario_details(self, scenario_name: str) -> Optional[PolicyScenario]:
        """
        Get detailed configuration for a specific scenario.

        Args:
            scenario_name: Name of the policy scenario

        Returns:
            PolicyScenario object or None if not found
        """
        return self.policy_scenarios.get(scenario_name)


def run_policy_analysis(
    base_results_path: str,
    scenario_names: List[str],
    jurisdiction: str = "AU",
    perspective: str = "health_system",
    config_path: Optional[str] = None,
    output_dir: str = "results/policy_analysis"
) -> PolicyToggleResults:
    """
    Convenience function to run policy realism analysis.

    Args:
        base_results_path: Path to base case results CSV
        scenario_names: List of policy scenario names to apply
        jurisdiction: Jurisdiction ('AU', 'NZ', or 'both')
        perspective: Perspective ('health_system' or 'societal')
        config_path: Path to custom policy configuration
        output_dir: Output directory

    Returns:
        PolicyToggleResults
    """
    # Load base results
    base_results = pd.read_csv(base_results_path)

    # Initialize engine
    engine = PolicyRealismEngine(config_path)

    # Apply policy toggles
    results = engine.apply_policy_toggles(
        base_results, scenario_names, jurisdiction, perspective
    )

    # Save results
    engine.save_policy_results(results, output_dir)

    return results
