"""
V4 Implementation Costs Engine

Dedicated engine for analyzing implementation costs including startup costs,
training costs, operational costs, and adoption costs for treatment adoption.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd


def get_cost_parameter(cost_parameters: Dict[str, Any], key: str, strategy: str, default: float) -> float:
    """Helper function to get cost parameter that may be dict or scalar."""
    param_value = cost_parameters.get(key, default)
    if isinstance(param_value, dict):
        return param_value.get(strategy, default)
    else:
        return param_value


@dataclass
class ImplementationCostResult:
    """Container for implementation cost analysis results."""
    
    startup_costs: pd.DataFrame         # One-time implementation costs
    operational_costs: pd.DataFrame     # Ongoing operational costs
    training_costs: pd.DataFrame        # Staff training and development costs
    adoption_costs: pd.DataFrame        # Patient adoption and engagement costs
    total_costs: pd.DataFrame           # Total implementation cost breakdown
    cost_amortization: pd.DataFrame     # Cost amortization schedules
    breakeven_analysis: pd.DataFrame    # Breakeven point calculations
    cost_effectiveness: pd.DataFrame    # Cost-effectiveness ratios
    sensitivity_analysis: pd.DataFrame  # Cost parameter sensitivity
    perspective: str
    jurisdiction: Optional[str]


def calculate_startup_costs(
    strategies: List[str],
    cost_parameters: Dict[str, Any]
) -> pd.DataFrame:
    """
    Calculate one-time startup costs for treatment implementation.
    
    Args:
        strategies: List of treatment strategies
        cost_parameters: Cost parameter dictionary
        
    Returns:
        DataFrame with startup cost breakdown
    """
    startup_costs = []
    
    for strategy in strategies:
        # Equipment and infrastructure costs
        equipment_cost = get_cost_parameter(cost_parameters, "startup_equipment", strategy, 0)
        
        # Facility modifications
        facility_mods = get_cost_parameter(cost_parameters, "facility_modifications", strategy, 0)
        
        # Regulatory and licensing costs
        regulatory_cost = get_cost_parameter(cost_parameters, "regulatory_costs", strategy, 5000)
        
        # Initial marketing and outreach
        marketing_cost = get_cost_parameter(cost_parameters, "initial_marketing", strategy, 10000)
        
        # IT system setup
        it_setup = get_cost_parameter(cost_parameters, "it_setup", strategy, 2000)
        
        total_startup = (equipment_cost + facility_mods + regulatory_cost + 
                        marketing_cost + it_setup)
        
        startup_costs.append({
            "strategy": strategy,
            "equipment_cost": equipment_cost,
            "facility_modifications": facility_mods,
            "regulatory_costs": regulatory_cost,
            "initial_marketing": marketing_cost,
            "it_setup": it_setup,
            "total_startup": total_startup
        })
    
    return pd.DataFrame(startup_costs)


def calculate_training_costs(
    strategies: List[str],
    treatment_volumes: pd.DataFrame,
    cost_parameters: Dict[str, Any]
) -> pd.DataFrame:
    """
    Calculate staff training and development costs.
    
    Args:
        strategies: List of treatment strategies
        treatment_volumes: DataFrame with expected treatment volumes
        cost_parameters: Cost parameter dictionary
        
    Returns:
        DataFrame with training cost breakdown
    """
    training_costs = []
    
    for strategy in strategies:
        # Get expected annual volume
        volume_row = treatment_volumes[treatment_volumes["strategy"] == strategy]
        if len(volume_row) > 0:
            annual_patients = volume_row["annual_volume"].iloc[0]
        else:
            annual_patients = 100  # Default assumption
        
        # Estimate staff requirements based on patient volume
        # Assume 1 staff member per 200 patients per year
        staff_needed = max(1, annual_patients / 200)
        
        # Training hours per staff member
        training_hours_per_staff = get_cost_parameter(cost_parameters, "training_hours_per_staff", strategy, 40)
        total_training_hours = training_hours_per_staff * staff_needed
        
        # Hourly training cost
        hourly_rate = get_cost_parameter(cost_parameters, "staff_hourly_rate", strategy, 75)
        training_cost = total_training_hours * hourly_rate
        
        # Additional training materials and certification
        materials_cost = get_cost_parameter(cost_parameters, "training_materials", strategy, 500)
        certification_cost = get_cost_parameter(cost_parameters, "certification_cost", strategy, 1000)
        
        # Ongoing professional development (annual)
        ongoing_training = get_cost_parameter(cost_parameters, "ongoing_training_annual", strategy, 2000)
        
        total_training = training_cost + materials_cost + certification_cost
        
        training_costs.append({
            "strategy": strategy,
            "annual_patients": annual_patients,
            "staff_needed": staff_needed,
            "training_hours_per_staff": training_hours_per_staff,
            "total_training_hours": total_training_hours,
            "training_labor_cost": training_cost,
            "materials_cost": materials_cost,
            "certification_cost": certification_cost,
            "ongoing_training_annual": ongoing_training,
            "total_initial_training": total_training
        })
    
    return pd.DataFrame(training_costs)


def calculate_operational_costs(
    strategies: List[str],
    treatment_volumes: pd.DataFrame,
    cost_parameters: Dict[str, Any]
) -> pd.DataFrame:
    """
    Calculate ongoing operational costs.
    
    Args:
        strategies: List of treatment strategies
        treatment_volumes: DataFrame with expected treatment volumes
        cost_parameters: Cost parameter dictionary
        
    Returns:
        DataFrame with operational cost breakdown
    """
    operational_costs = []
    
    for strategy in strategies:
        # Get expected annual volume
        volume_row = treatment_volumes[treatment_volumes["strategy"] == strategy]
        if len(volume_row) > 0:
            annual_patients = volume_row["annual_volume"].iloc[0]
        else:
            annual_patients = 100  # Default assumption
        
        # Supplies and consumables per patient
        supplies_per_patient = get_cost_parameter(cost_parameters, "supplies_per_patient", strategy, 100)
        supplies_cost = supplies_per_patient * annual_patients
        
        # Monitoring and follow-up costs per patient
        monitoring_per_patient = get_cost_parameter(cost_parameters, "monitoring_per_patient", strategy, 50)
        monitoring_cost = monitoring_per_patient * annual_patients
        
        # Equipment maintenance (annual)
        maintenance_annual = get_cost_parameter(cost_parameters, "equipment_maintenance", strategy, 5000)
        
        # Quality assurance and auditing
        qa_cost = get_cost_parameter(cost_parameters, "quality_assurance", strategy, 2000)
        
        # Administrative overhead
        admin_overhead = get_cost_parameter(cost_parameters, "administrative_overhead", strategy, 10000)
        
        # Utilities and facility costs (allocated per strategy)
        utilities_allocated = get_cost_parameter(cost_parameters, "utilities_allocated", strategy, 3000)
        
        total_operational = (supplies_cost + monitoring_cost + maintenance_annual + 
                           qa_cost + admin_overhead + utilities_allocated)
        
        operational_costs.append({
            "strategy": strategy,
            "annual_patients": annual_patients,
            "supplies_cost": supplies_cost,
            "monitoring_cost": monitoring_cost,
            "maintenance_annual": maintenance_annual,
            "quality_assurance": qa_cost,
            "administrative_overhead": admin_overhead,
            "utilities_allocated": utilities_allocated,
            "total_operational_annual": total_operational
        })
    
    return pd.DataFrame(operational_costs)


def calculate_adoption_costs(
    strategies: List[str],
    treatment_volumes: pd.DataFrame,
    cost_parameters: Dict[str, Any]
) -> pd.DataFrame:
    """
    Calculate patient adoption and engagement costs.
    
    Args:
        strategies: List of treatment strategies
        treatment_volumes: DataFrame with expected treatment volumes
        cost_parameters: Cost parameter dictionary
        
    Returns:
        DataFrame with adoption cost breakdown
    """
    adoption_costs = []
    
    for strategy in strategies:
        # Get expected annual volume
        volume_row = treatment_volumes[treatment_volumes["strategy"] == strategy]
        if len(volume_row) > 0:
            annual_patients = volume_row["annual_volume"].iloc[0]
        else:
            annual_patients = 100  # Default assumption
        
        # Patient education and counseling
        education_per_patient = get_cost_parameter(cost_parameters, "patient_education_per_patient", strategy, 25)
        education_cost = education_per_patient * annual_patients
        
        # Outreach and marketing (ongoing)
        outreach_annual = get_cost_parameter(cost_parameters, "outreach_marketing_annual", strategy, 5000)
        
        # Care coordination costs
        coordination_per_patient = get_cost_parameter(cost_parameters, "care_coordination_per_patient", strategy, 15)
        coordination_cost = coordination_per_patient * annual_patients
        
        # Transportation assistance (for some patients)
        transport_assistance_rate = get_cost_parameter(cost_parameters, "transport_assistance_rate", None, 0.1)  # 10% of patients
        transport_per_patient = get_cost_parameter(cost_parameters, "transport_per_patient", strategy, 50)
        transport_cost = transport_assistance_rate * annual_patients * transport_per_patient
        
        # Follow-up and retention programs
        retention_per_patient = get_cost_parameter(cost_parameters, "retention_program_per_patient", strategy, 10)
        retention_cost = retention_per_patient * annual_patients
        
        total_adoption = education_cost + outreach_annual + coordination_cost + transport_cost + retention_cost
        
        adoption_costs.append({
            "strategy": strategy,
            "annual_patients": annual_patients,
            "patient_education": education_cost,
            "outreach_marketing": outreach_annual,
            "care_coordination": coordination_cost,
            "transport_assistance": transport_cost,
            "retention_programs": retention_cost,
            "total_adoption_annual": total_adoption,
            "adoption_rate_target": cost_parameters.get("adoption_rate_target", 0.7)
        })
    
    return pd.DataFrame(adoption_costs)


def calculate_cost_amortization(
    startup_costs: pd.DataFrame,
    operational_costs: pd.DataFrame,
    training_costs: pd.DataFrame,
    adoption_costs: pd.DataFrame,
    time_horizon: int = 5
) -> pd.DataFrame:
    """
    Calculate cost amortization schedule over time.
    
    Args:
        startup_costs: Startup cost DataFrame
        operational_costs: Operational cost DataFrame
        training_costs: Training cost DataFrame
        adoption_costs: Adoption cost DataFrame
        time_horizon: Analysis time horizon in years
        
    Returns:
        DataFrame with annual cost amortization
    """
    amortization_schedule = []
    
    strategies = startup_costs["strategy"].unique()
    
    for strategy in strategies:
        startup = startup_costs[startup_costs["strategy"] == strategy]["total_startup"].iloc[0]
        operational = operational_costs[operational_costs["strategy"] == strategy]["total_operational_annual"].iloc[0]
        training = training_costs[training_costs["strategy"] == strategy]["total_initial_training"].iloc[0]
        adoption = adoption_costs[adoption_costs["strategy"] == strategy]["total_adoption_annual"].iloc[0]
        
        # Amortize startup costs over time horizon
        annual_startup_amortization = startup / time_horizon
        
        for year in range(1, time_horizon + 1):
            # Training costs only in year 1
            training_annual = training if year == 1 else 0
            
            # Operational and adoption costs are ongoing
            total_annual = (annual_startup_amortization + operational + 
                          training_annual + adoption)
            
            amortization_schedule.append({
                "strategy": strategy,
                "year": year,
                "startup_amortization": annual_startup_amortization,
                "operational_cost": operational,
                "training_cost": training_annual,
                "adoption_cost": adoption,
                "total_annual_cost": total_annual,
                "cumulative_cost": total_annual * year  # Simplified cumulative
            })
    
    return pd.DataFrame(amortization_schedule)


def perform_breakeven_analysis(
    operational_costs: pd.DataFrame,
    cost_parameters: Dict[str, Any],
    time_horizon: int = 5
) -> pd.DataFrame:
    """
    Perform breakeven analysis for implementation costs.
    
    Args:
        operational_costs: Operational cost DataFrame
        cost_parameters: Cost parameter dictionary
        time_horizon: Analysis time horizon in years
        
    Returns:
        DataFrame with breakeven analysis results
    """
    breakeven_results = []
    
    for _, row in operational_costs.iterrows():
        strategy = row["strategy"]
        annual_patients = row["annual_patients"]
        annual_operational_cost = row["total_operational_annual"]
        
        # Estimate revenue per patient (simplified assumption)
        revenue_per_patient = get_cost_parameter(cost_parameters, "revenue_per_patient", strategy, 2000)
        annual_revenue = annual_patients * revenue_per_patient
        
        # Calculate annual profit/loss
        annual_profit = annual_revenue - annual_operational_cost
        
        # Find breakeven point (when cumulative profit becomes positive)
        cumulative_profit = 0
        breakeven_year = None
        
        for year in range(1, time_horizon + 1):
            # Add startup costs in year 1
            if year == 1:
                startup_cost = get_cost_parameter(cost_parameters, "startup_equipment", strategy, 0)
                cumulative_profit -= startup_cost
            
            cumulative_profit += annual_profit
            
            if breakeven_year is None and cumulative_profit >= 0:
                breakeven_year = year
        
        # Calculate profitability metrics
        profitability_ratio = annual_revenue / annual_operational_cost if annual_operational_cost > 0 else float('inf')
        roi = (annual_profit / annual_operational_cost) if annual_operational_cost > 0 else float('inf')
        
        breakeven_results.append({
            "strategy": strategy,
            "annual_patients": annual_patients,
            "revenue_per_patient": revenue_per_patient,
            "annual_revenue": annual_revenue,
            "annual_operational_cost": annual_operational_cost,
            "annual_profit": annual_profit,
            "breakeven_year": breakeven_year or f">{time_horizon}",
            "profitability_ratio": profitability_ratio,
            "roi": roi,
            "payback_period_years": (get_cost_parameter(cost_parameters, "startup_equipment", strategy, 0) / 
                                   annual_profit) if annual_profit > 0 else float('inf')
        })
    
    return pd.DataFrame(breakeven_results)


def perform_cost_sensitivity_analysis(
    base_costs: pd.DataFrame,
    sensitivity_ranges: Dict[str, Tuple[float, float]] = None
) -> pd.DataFrame:
    """
    Perform sensitivity analysis on cost parameters.
    
    Args:
        base_costs: Base cost DataFrame
        sensitivity_ranges: Dictionary of parameter ranges for sensitivity analysis
        
    Returns:
        DataFrame with sensitivity analysis results
    """
    if sensitivity_ranges is None:
        sensitivity_ranges = {
            "startup_cost": (0.5, 2.0),      # ±50% to ±100%
            "operational_cost": (0.7, 1.5),  # -30% to +50%
            "training_cost": (0.8, 1.3),     # -20% to +30%
            "adoption_cost": (0.6, 1.8)      # -40% to +80%
        }
    
    sensitivity_results = []
    
    for _, row in base_costs.iterrows():
        strategy = row["strategy"]
        base_total = row["total_5year_cost"]
        
        for param, (low_mult, high_mult) in sensitivity_ranges.items():
            if param in row.index:
                base_param_cost = row[param]
                
                # Low scenario
                low_cost = base_total - base_param_cost + (base_param_cost * low_mult)
                low_change = ((low_cost - base_total) / base_total) * 100
                
                # High scenario
                high_cost = base_total - base_param_cost + (base_param_cost * high_mult)
                high_change = ((high_cost - base_total) / base_total) * 100
                
                sensitivity_results.append({
                    "strategy": strategy,
                    "parameter": param,
                    "base_cost": base_total,
                    "low_scenario_cost": low_cost,
                    "high_scenario_cost": high_cost,
                    "low_change_percent": low_change,
                    "high_change_percent": high_change,
                    "sensitivity_range": high_change - low_change
                })
    
    return pd.DataFrame(sensitivity_results)


def analyze_implementation_costs(
    treatment_volumes: pd.DataFrame,
    cost_parameters: Dict[str, Any],
    time_horizon: int = 5
) -> ImplementationCostResult:
    """
    Comprehensive implementation cost analysis.
    
    Args:
        treatment_volumes: DataFrame with expected treatment volumes
        cost_parameters: Dictionary of cost parameters
        time_horizon: Implementation time horizon in years
        
    Returns:
        Implementation cost analysis results
    """
    strategies = treatment_volumes["strategy"].unique()
    
    # Calculate component costs
    startup_costs = calculate_startup_costs(strategies, cost_parameters)
    training_costs = calculate_training_costs(strategies, treatment_volumes, cost_parameters)
    operational_costs = calculate_operational_costs(strategies, treatment_volumes, cost_parameters)
    adoption_costs = calculate_adoption_costs(strategies, treatment_volumes, cost_parameters)
    
    # Calculate total costs
    total_costs = []
    for strategy in strategies:
        startup = startup_costs[startup_costs["strategy"] == strategy]["total_startup"].iloc[0]
        training = training_costs[training_costs["strategy"] == strategy]["total_initial_training"].iloc[0]
        operational = operational_costs[operational_costs["strategy"] == strategy]["total_operational_annual"].iloc[0]
        adoption = adoption_costs[adoption_costs["strategy"] == strategy]["total_adoption_annual"].iloc[0]
        
        total_5year = startup + training + (operational + adoption) * time_horizon
        
        total_costs.append({
            "strategy": strategy,
            "total_startup": startup,
            "total_training": training,
            "annual_operational": operational,
            "annual_adoption": adoption,
            "total_5year_cost": total_5year,
            "cost_per_patient_year1": (startup/time_horizon + training + operational + adoption) / 
                                    treatment_volumes[treatment_volumes["strategy"] == strategy]["annual_volume"].iloc[0]
        })
    
    total_costs_df = pd.DataFrame(total_costs)
    
    # Calculate amortization schedule
    cost_amortization = calculate_cost_amortization(
        startup_costs, operational_costs, training_costs, adoption_costs, time_horizon
    )
    
    # Perform breakeven analysis
    breakeven_analysis = perform_breakeven_analysis(operational_costs, cost_parameters, time_horizon)
    
    # Calculate cost-effectiveness ratios (simplified)
    cost_effectiveness = []
    for strategy in strategies:
        total_5year = total_costs_df[total_costs_df["strategy"] == strategy]["total_5year_cost"].iloc[0]
        annual_patients = treatment_volumes[treatment_volumes["strategy"] == strategy]["annual_volume"].iloc[0]
        total_patients_5year = annual_patients * time_horizon
        
        # Simplified QALY assumption (placeholder)
        qaly_per_patient = get_cost_parameter(cost_parameters, "qaly_per_patient", strategy, 0.5)
        total_qaly = total_patients_5year * qaly_per_patient
        
        cost_effectiveness.append({
            "strategy": strategy,
            "total_cost_5year": total_5year,
            "total_qaly_5year": total_qaly,
            "cost_per_qaly": total_5year / total_qaly if total_qaly > 0 else float('inf'),
            "icer_vs_usual_care": None  # Would need comparator analysis
        })
    
    cost_effectiveness_df = pd.DataFrame(cost_effectiveness)
    
    # Perform sensitivity analysis
    sensitivity_analysis = perform_cost_sensitivity_analysis(total_costs_df)
    
    return ImplementationCostResult(
        startup_costs=startup_costs,
        operational_costs=operational_costs,
        training_costs=training_costs,
        adoption_costs=adoption_costs,
        total_costs=total_costs_df,
        cost_amortization=cost_amortization,
        breakeven_analysis=breakeven_analysis,
        cost_effectiveness=cost_effectiveness_df,
        sensitivity_analysis=sensitivity_analysis,
        perspective="health_system",
        jurisdiction=None
    )