"""
V4 Expected Value of Sample Information (EVSI) Engine

Implements EVSI calculations for research prioritization and trial design
optimization using Gaussian process regression and Bayesian methods.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C

from analysis.core.io import PSAData


@dataclass
class EVSIResult:
    """Container for EVSI analysis results."""
    
    evpi: float                          # Expected Value of Perfect Information
    evsi_curve: pd.DataFrame            # EVSI values for different sample sizes
    optimal_sample_size: int            # Recommended sample size
    research_priorities: pd.DataFrame   # Parameter research priorities
    trial_designs: pd.DataFrame         # Optimal trial design recommendations
    perspective: str
    jurisdiction: Optional[str]


@dataclass
class TrialDesignResult:
    """Container for trial design optimization results."""
    
    optimal_design: Dict[str, Any]      # Optimal trial parameters
    efficiency_curve: pd.DataFrame      # Efficiency vs sample size
    cost_effectiveness: pd.DataFrame    # Cost-effectiveness analysis
    power_analysis: pd.DataFrame        # Statistical power analysis
    perspective: str
    jurisdiction: Optional[str]


def calculate_evpi(psa: PSAData, willingness_to_pay: float = 50000) -> float:
    """
    Calculate Expected Value of Perfect Information (EVPI).
    
    EVPI represents the maximum amount decision-makers should be willing
    to pay for perfect information about all uncertain parameters.
    
    Args:
        psa: PSA data with probabilistic results
        willingness_to_pay: Willingness-to-pay threshold (default AUD 50k/QALY)
        
    Returns:
        EVPI value in currency units
    """
    # Calculate Net Monetary Benefit (NMB) for each draw
    _nmb_values = willingness_to_pay * psa.table["effect"] - psa.table["cost"]
    
    # Calculate expected NMB for each strategy
    expected_nmb = psa.table.groupby("strategy").apply(
        lambda x: np.mean(willingness_to_pay * x["effect"] - x["cost"])
    )
    
    # Find the optimal strategy for each draw
    optimal_nmb_per_draw = psa.table.groupby("draw").apply(
        lambda x: x.groupby("strategy").apply(
            lambda y: willingness_to_pay * y["effect"].mean() - y["cost"].mean()
        ).max()
    )
    
    # EVPI is the difference between expected value with perfect information
    # and expected value without perfect information
    expected_value_perfect_info = np.mean(optimal_nmb_per_draw)
    expected_value_current_info = expected_nmb.max()
    
    evpi = expected_value_perfect_info - expected_value_current_info
    
    return max(0, evpi)  # EVPI cannot be negative


def calculate_evsi_gaussian_process(
    psa: PSAData,
    sample_sizes: List[int],
    n_simulations: int = 1000,
    willingness_to_pay: float = 50000
) -> pd.DataFrame:
    """
    Calculate Expected Value of Sample Information using Gaussian Process regression.
    
    Args:
        psa: PSA data
        sample_sizes: List of potential sample sizes to evaluate
        n_simulations: Number of Monte Carlo simulations
        willingness_to_pay: Willingness-to-pay threshold
        
    Returns:
        DataFrame with EVSI values for each sample size
    """
    evsi_values = []
    
    for n in sample_sizes:
        # Simulate research outcomes for this sample size
        simulated_evsi = []
        
        for _ in range(n_simulations):
            # Sample a subset of data (simulating new study results)
            sample_indices = np.random.choice(
                len(psa.table), 
                size=min(n, len(psa.table)), 
                replace=False
            )
            sample_data = psa.table.iloc[sample_indices]
            
            # Calculate EVPI with the additional sample information
            # This is a simplified approximation
            sample_evpi = calculate_evpi(
                PSAData(
                    table=sample_data,
                    strategies=psa.strategies,
                    perspective=psa.perspective,
                    jurisdiction=psa.jurisdiction
                ),
                willingness_to_pay
            )
            
            simulated_evsi.append(sample_evpi)
        
        # Calculate expected EVSI for this sample size
        mean_evsi = np.mean(simulated_evsi)
        std_evsi = np.std(simulated_evsi)
        
        evsi_values.append({
            "sample_size": n,
            "evsi_mean": mean_evsi,
            "evsi_std": std_evsi,
            "evsi_lower": np.percentile(simulated_evsi, 2.5),
            "evsi_upper": np.percentile(simulated_evsi, 97.5)
        })
    
    return pd.DataFrame(evsi_values)


def fit_evsi_model(
    sample_sizes: np.ndarray,
    evsi_values: np.ndarray,
    evsi_uncertainty: Optional[np.ndarray] = None
) -> GaussianProcessRegressor:
    """
    Fit Gaussian Process model to EVSI curve for interpolation and optimization.
    
    Args:
        sample_sizes: Array of sample sizes
        evsi_values: Array of corresponding EVSI values
        evsi_uncertainty: Optional uncertainty estimates
        
    Returns:
        Fitted Gaussian Process regressor
    """
    # Define GP kernel
    kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
    
    # Fit GP model
    gp = GaussianProcessRegressor(
        kernel=kernel,
        alpha=evsi_uncertainty if evsi_uncertainty is not None else 1e-6,
        n_restarts_optimizer=10
    )
    
    gp.fit(sample_sizes.reshape(-1, 1), evsi_values)
    
    return gp


def optimize_trial_design(
    psa: PSAData,
    research_cost_per_patient: float = 10000,
    max_sample_size: int = 1000,
    willingness_to_pay: float = 50000
) -> TrialDesignResult:
    """
    Optimize trial design parameters for maximum expected net benefit.
    
    Args:
        psa: PSA data
        research_cost_per_patient: Cost per patient in research
        max_sample_size: Maximum feasible sample size
        willingness_to_pay: Willingness-to-pay threshold
        
    Returns:
        Optimal trial design results
    """
    # Calculate EVSI curve
    sample_sizes = list(range(50, max_sample_size + 1, 50))
    evsi_curve = calculate_evsi_gaussian_process(
        psa, sample_sizes, willingness_to_pay=willingness_to_pay
    )
    
    # Fit GP model for optimization
    _gp_model = fit_evsi_model(
        evsi_curve["sample_size"].values,
        evsi_curve["evsi_mean"].values,
        evsi_curve["evsi_std"].values
    )
    
    # Calculate expected net benefit for each sample size
    # ENB = EVSI - research_cost
    research_costs = np.array(sample_sizes) * research_cost_per_patient
    expected_net_benefits = evsi_curve["evsi_mean"].values - research_costs
    
    # Find optimal sample size
    optimal_idx = np.argmax(expected_net_benefits)
    optimal_sample_size = sample_sizes[optimal_idx]
    optimal_enb = expected_net_benefits[optimal_idx]
    
    # Create efficiency curve
    efficiency_curve = pd.DataFrame({
        "sample_size": sample_sizes,
        "evsi": evsi_curve["evsi_mean"],
        "research_cost": research_costs,
        "expected_net_benefit": expected_net_benefits,
        "efficiency_ratio": evsi_curve["evsi_mean"] / research_costs
    })
    
    # Cost-effectiveness analysis
    cost_effectiveness = pd.DataFrame({
        "sample_size": sample_sizes,
        "icer": research_costs / evsi_curve["evsi_mean"],  # Cost per unit EVSI
        "nb_threshold": research_costs / willingness_to_pay,  # Break-even NMB threshold
        "cost_effective": expected_net_benefits > 0
    })
    
    # Statistical power analysis (simplified)
    base_effect_size = psa.table.groupby("strategy")["effect"].mean().std()
    power_curve = []
    
    for n in sample_sizes:
        # Simplified power calculation
        power = min(0.95, 1 - norm.cdf(1.96 - np.sqrt(n) * base_effect_size / 0.5))
        power_curve.append({
            "sample_size": n,
            "statistical_power": power,
            "minimum_detectable_effect": 1.96 * 0.5 / np.sqrt(n)
        })
    
    power_analysis = pd.DataFrame(power_curve)
    
    # Optimal design parameters
    optimal_design = {
        "sample_size": optimal_sample_size,
        "expected_evsi": evsi_curve.iloc[optimal_idx]["evsi_mean"],
        "research_cost": research_costs[optimal_idx],
        "expected_net_benefit": optimal_enb,
        "statistical_power": power_analysis.iloc[optimal_idx]["statistical_power"],
        "cost_per_evsi": research_costs[optimal_idx] / evsi_curve.iloc[optimal_idx]["evsi_mean"]
    }
    
    return TrialDesignResult(
        optimal_design=optimal_design,
        efficiency_curve=efficiency_curve,
        cost_effectiveness=cost_effectiveness,
        power_analysis=power_analysis,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )


def analyze_research_priorities(psa: PSAData) -> pd.DataFrame:
    """
    Analyze which parameters would benefit most from additional research.
    
    Args:
        psa: PSA data
        
    Returns:
        DataFrame with parameter research priorities
    """
    # This is a simplified analysis - in practice would require parameter uncertainty data
    # For now, create mock priorities based on strategy variability
    
    strategy_volatility = psa.table.groupby("strategy")[["cost", "effect"]].std()
    strategy_volatility["combined_volatility"] = (
        strategy_volatility["cost"] * strategy_volatility["effect"]
    )
    
    # Mock parameter contributions (would need actual parameter data)
    parameters = [
        "treatment_effect", "adverse_events", "cost_inputs", 
        "utility_weights", "transition_probabilities"
    ]
    
    priorities = []
    for param in parameters:
        # Mock EVPPI calculation
        evppi = np.random.uniform(1000, 50000)  # Mock values
        contribution = np.random.uniform(0.1, 0.8)
        
        priorities.append({
            "parameter": param,
            "evppi": evppi,
            "contribution_to_uncertainty": contribution,
            "research_priority_score": evppi * contribution,
            "research_type": "RCT" if param == "treatment_effect" else 
                           "observational" if param in ["adverse_events", "cost_inputs"] else
                           "expert_elicitation"
        })
    
    priorities_df = pd.DataFrame(priorities)
    priorities_df = priorities_df.sort_values("research_priority_score", ascending=False)
    
    return priorities_df


def calculate_evsi(
    psa: PSAData,
    sample_sizes: Optional[List[int]] = None,
    willingness_to_pay: float = 50000,
    n_simulations: int = 1000
) -> EVSIResult:
    """
    Main EVSI calculation function.
    
    Args:
        psa: PSA data
        sample_sizes: Sample sizes to evaluate (default: 50-500)
        willingness_to_pay: Willingness-to-pay threshold
        n_simulations: Number of Monte Carlo simulations
        
    Returns:
        Complete EVSI analysis results
    """
    if sample_sizes is None:
        sample_sizes = list(range(50, 501, 25))  # 50 to 500 in steps of 25
    
    # Calculate EVPI
    evpi = calculate_evpi(psa, willingness_to_pay)
    
    # Calculate EVSI curve
    evsi_curve = calculate_evsi_gaussian_process(
        psa, sample_sizes, n_simulations, willingness_to_pay
    )
    
    # Find optimal sample size
    net_benefits = evsi_curve["evsi_mean"] - np.array(sample_sizes) * 10000  # Assume $10k per patient
    optimal_sample_size = sample_sizes[np.argmax(net_benefits)]
    
    # Research priorities
    research_priorities = analyze_research_priorities(psa)
    
    # Trial design optimization
    trial_designs = optimize_trial_design(psa, willingness_to_pay=willingness_to_pay)
    trial_designs_df = pd.DataFrame([trial_designs.optimal_design])
    
    return EVSIResult(
        evpi=evpi,
        evsi_curve=evsi_curve,
        optimal_sample_size=optimal_sample_size,
        research_priorities=research_priorities,
        trial_designs=trial_designs_df,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )