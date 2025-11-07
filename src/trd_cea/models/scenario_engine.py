"""
V4 Scenario and Structural Analysis Engine

Implements alternative scenario modeling and structural sensitivity analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Callable

import pandas as pd


@dataclass
class ScenarioDefinition:
    """Definition of an analysis scenario."""
    
    name: str
    description: str
    parameters: Dict[str, float]
    structural_assumptions: Optional[Dict[str, str]] = None


@dataclass
class ScenarioResult:
    """Container for scenario analysis results."""
    
    scenario_name: str
    outcomes: Dict[str, float]
    comparison_to_base: Dict[str, float]


@dataclass
class StructuralSensitivityResult:
    """Container for structural sensitivity analysis results."""
    
    model_variant: str
    outcomes: pd.DataFrame
    comparison_to_base: pd.DataFrame


def define_standard_scenarios() -> List[ScenarioDefinition]:
    """
    Define standard analysis scenarios.
    
    Returns:
        List of standard scenarios
    """
    scenarios = [
        ScenarioDefinition(
            name="Base Case",
            description="Base case analysis with standard assumptions",
            parameters={
                'discount_rate': 0.05,
                'time_horizon': 10,
                'wtp_threshold': 50000
            }
        ),
        ScenarioDefinition(
            name="Conservative",
            description="Conservative assumptions favoring standard care",
            parameters={
                'discount_rate': 0.05,
                'time_horizon': 5,
                'wtp_threshold': 30000,
                'treatment_efficacy_multiplier': 0.8
            }
        ),
        ScenarioDefinition(
            name="Optimistic",
            description="Optimistic assumptions for novel therapies",
            parameters={
                'discount_rate': 0.03,
                'time_horizon': 15,
                'wtp_threshold': 75000,
                'treatment_efficacy_multiplier': 1.2
            }
        ),
        ScenarioDefinition(
            name="Societal Perspective",
            description="Broader societal costs included",
            parameters={
                'discount_rate': 0.05,
                'time_horizon': 10,
                'wtp_threshold': 50000,
                'include_productivity': True,
                'include_informal_care': True
            }
        ),
        ScenarioDefinition(
            name="Short Time Horizon",
            description="Short-term analysis (5 years)",
            parameters={
                'discount_rate': 0.05,
                'time_horizon': 5,
                'wtp_threshold': 50000
            }
        ),
        ScenarioDefinition(
            name="Long Time Horizon",
            description="Long-term analysis (20 years)",
            parameters={
                'discount_rate': 0.05,
                'time_horizon': 20,
                'wtp_threshold': 50000
            }
        ),
        ScenarioDefinition(
            name="No Discounting",
            description="Analysis without discounting",
            parameters={
                'discount_rate': 0.0,
                'time_horizon': 10,
                'wtp_threshold': 50000
            }
        ),
        ScenarioDefinition(
            name="High Relapse Rate",
            description="Pessimistic relapse assumptions",
            parameters={
                'discount_rate': 0.05,
                'time_horizon': 10,
                'wtp_threshold': 50000,
                'relapse_rate_multiplier': 1.5
            }
        ),
        ScenarioDefinition(
            name="Low Relapse Rate",
            description="Optimistic relapse assumptions",
            parameters={
                'discount_rate': 0.05,
                'time_horizon': 10,
                'wtp_threshold': 50000,
                'relapse_rate_multiplier': 0.5
            }
        )
    ]
    
    return scenarios


def run_scenario_analysis(
    scenarios: List[ScenarioDefinition],
    outcome_function: Callable[[Dict[str, float]], Dict[str, float]],
    base_scenario_name: str = "Base Case"
) -> List[ScenarioResult]:
    """
    Run scenario analysis.
    
    Args:
        scenarios: List of scenario definitions
        outcome_function: Function that calculates outcomes given parameters
        base_scenario_name: Name of base case scenario
    
    Returns:
        List of ScenarioResult
    """
    results = []
    base_outcomes = None
    
    # Find base case
    for scenario in scenarios:
        if scenario.name == base_scenario_name:
            base_outcomes = outcome_function(scenario.parameters)
            break
    
    # Run all scenarios
    for scenario in scenarios:
        outcomes = outcome_function(scenario.parameters)
        
        # Calculate comparison to base
        if base_outcomes and scenario.name != base_scenario_name:
            comparison = {
                key: outcomes[key] - base_outcomes[key]
                for key in outcomes.keys()
            }
        else:
            comparison = {key: 0.0 for key in outcomes.keys()}
        
        results.append(ScenarioResult(
            scenario_name=scenario.name,
            outcomes=outcomes,
            comparison_to_base=comparison
        ))
    
    return results


def structural_sensitivity_analysis(
    model_variants: Dict[str, Callable],
    base_model_name: str = "Base Model"
) -> List[StructuralSensitivityResult]:
    """
    Perform structural sensitivity analysis.
    
    Tests different model structures (e.g., different state definitions,
    transition assumptions, utility mappings).
    
    Args:
        model_variants: Dictionary of model names to model functions
        base_model_name: Name of base model
    
    Returns:
        List of StructuralSensitivityResult
    """
    results = []
    base_outcomes = None
    
    # Run base model
    if base_model_name in model_variants:
        base_outcomes = model_variants[base_model_name]()
    
    # Run all model variants
    for model_name, model_function in model_variants.items():
        outcomes = model_function()
        
        # Convert to DataFrame if not already
        if isinstance(outcomes, dict):
            outcomes_df = pd.DataFrame([outcomes])
        else:
            outcomes_df = outcomes
        
        # Calculate comparison to base
        if base_outcomes is not None and model_name != base_model_name:
            if isinstance(base_outcomes, dict):
                base_df = pd.DataFrame([base_outcomes])
            else:
                base_df = base_outcomes
            
            comparison_df = outcomes_df - base_df
        else:
            comparison_df = pd.DataFrame()
        
        results.append(StructuralSensitivityResult(
            model_variant=model_name,
            outcomes=outcomes_df,
            comparison_to_base=comparison_df
        ))
    
    return results


def define_structural_variants() -> Dict[str, str]:
    """
    Define standard structural model variants.
    
    Returns:
        Dictionary of variant names to descriptions
    """
    variants = {
        "Three-State Model": "Depressed, Remission, Death",
        "Four-State Model": "Depressed, Partial Response, Remission, Death",
        "Five-State Model": "Depressed, Partial Response, Remission, Relapse, Death",
        "With Tunnel States": "Time-dependent transitions using tunnel states",
        "Without Tunnel States": "Time-independent transitions",
        "Linear Utility": "Linear utility mapping",
        "Non-Linear Utility": "Non-linear utility with diminishing returns",
        "Constant Relapse": "Constant relapse rate over time",
        "Time-Varying Relapse": "Relapse rate varies with time since remission"
    }
    
    return variants


def save_scenario_results(
    scenario_results: List[ScenarioResult],
    output_dir: Path
) -> None:
    """
    Save scenario analysis results.
    
    Args:
        scenario_results: List of scenario results
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Combine all results
    all_results = []
    for result in scenario_results:
        row = {'scenario': result.scenario_name}
        row.update(result.outcomes)
        row.update({f"{k}_vs_base": v for k, v in result.comparison_to_base.items()})
        all_results.append(row)
    
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(output_dir / "scenario_analysis.csv", index=False)


def save_structural_sensitivity_results(
    structural_results: List[StructuralSensitivityResult],
    output_dir: Path
) -> None:
    """
    Save structural sensitivity analysis results.
    
    Args:
        structural_results: List of structural sensitivity results
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save each variant's results
    for result in structural_results:
        variant_name = result.model_variant.replace(" ", "_").lower()
        
        result.outcomes.to_csv(
            output_dir / f"structural_{variant_name}_outcomes.csv",
            index=False
        )
        
        if not result.comparison_to_base.empty:
            result.comparison_to_base.to_csv(
                output_dir / f"structural_{variant_name}_comparison.csv",
                index=False
            )
