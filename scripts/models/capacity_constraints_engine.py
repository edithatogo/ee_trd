"""
V4 Capacity Constraints and Implementation Features Engine

Implements capacity constraints modeling, implementation costs, and health system
capacity analysis for treatment adoption and scaling.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd
import math


@dataclass
class CapacityConstraintResult:
    """Container for capacity constraint analysis results."""
    
    waiting_times: pd.DataFrame         # Waiting time distributions by strategy
    utilization_rates: pd.DataFrame     # Resource utilization analysis
    bottleneck_analysis: pd.DataFrame   # Bottleneck identification
    capacity_requirements: pd.DataFrame # Required capacity scaling
    queueing_metrics: pd.DataFrame      # Queueing theory metrics
    perspective: str
    jurisdiction: Optional[str]


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
    perspective: str
    jurisdiction: Optional[str]


class QueueingModel:
    """Queueing theory models for capacity analysis."""
    
    def __init__(self, arrival_rate: float, service_rate: float, servers: int = 1):
        """
        Initialize queueing model.
        
        Args:
            arrival_rate: Patient arrival rate (λ)
            service_rate: Service completion rate (μ)
            servers: Number of servers (c)
        """
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.servers = servers
        self.utilization = arrival_rate / (servers * service_rate)
        
        # Validate stability
        if self.utilization >= 1:
            raise ValueError("System is unstable (ρ ≥ 1)")
    
    def waiting_time_distribution(self, n_patients: int = 10000) -> Dict[str, float]:
        """Calculate waiting time distribution metrics."""
        if self.servers == 1:
            # M/M/1 queue
            mean_waiting_time = self.utilization / (self.service_rate * (1 - self.utilization))
            _var_waiting_time = (self.utilization / (self.service_rate ** 2 * (1 - self.utilization) ** 2))
        else:
            # M/M/c queue approximation
            c = self.servers
            rho = self.utilization
            
            # Erlang C formula for probability of waiting
            def erlang_c(c, rho):
                if rho >= 1:
                    return 1
                sum_term = sum((c * rho) ** k / math.factorial(k) for k in range(c))
                return (c * rho) ** c / (math.factorial(c) * (1 - rho)) / (
                    sum_term + (c * rho) ** c / (math.factorial(c) * (1 - rho))
                )
            
            p_wait = erlang_c(c, rho)
            mean_waiting_time = p_wait / (c * self.service_rate * (1 - rho))
            _var_waiting_time = (p_wait * (1 + c * (1 - rho) * (c * rho) ** (c - 1) / 
                                         ((c * rho) ** c / math.factorial(c)) ** 2)) / (
                                         c * self.service_rate * (1 - rho)) ** 2
        
        # Generate sample waiting times
        if self.servers == 1:
            waiting_times = np.random.exponential(1 / (self.service_rate * (1 - self.utilization)), n_patients)
        else:
            # Approximation for M/M/c
            waiting_times = np.random.exponential(1 / (self.servers * self.service_rate * (1 - self.utilization)), n_patients)
        
        return {
            "mean_waiting_time": mean_waiting_time,
            "median_waiting_time": np.median(waiting_times),
            "p95_waiting_time": np.percentile(waiting_times, 95),
            "p99_waiting_time": np.percentile(waiting_times, 99),
            "max_waiting_time": np.max(waiting_times),
            "utilization_rate": self.utilization,
            "probability_waiting": p_wait if self.servers > 1 else self.utilization
        }


def analyze_capacity_constraints(
    treatment_demand: pd.DataFrame,
    resource_capacity: Dict[str, float],
    time_horizon: int = 365
) -> CapacityConstraintResult:
    """
    Analyze capacity constraints for treatment implementation.
    
    Args:
        treatment_demand: DataFrame with treatment demand by strategy
        resource_capacity: Dictionary of resource capacities
        time_horizon: Analysis time horizon in days
        
    Returns:
        Capacity constraint analysis results
    """
    strategies = treatment_demand["strategy"].unique()
    results = []
    
    for strategy in strategies:
        strategy_data = treatment_demand[treatment_demand["strategy"] == strategy]
        daily_demand = strategy_data["demand"].mean()
        
        # Estimate service rates based on treatment type
        service_rates = {
            "ECT": 1/3,      # 3 days per treatment course
            "KA-ECT": 1/2,   # 2 days per course
            "IV-KA": 1/1,    # 1 day per infusion
            "IN-EKA": 1/7,   # 1 week per course
            "PO-PSI": 1/42,  # 6 weeks per course
            "PO-KA": 1/30,   # 30 days per course
            "rTMS": 1/20,    # 20 days per course
            "UC+Li": 1/90,   # 90 days per course
            "UC+AA": 1/90,   # 90 days per course
            "Usual Care": 1/30  # 30 days per course
        }
        
        service_rate = service_rates.get(strategy, 1/30)  # Default to 30 days
        
        # Analyze different capacity scenarios
        capacity_scenarios = [0.5, 0.75, 1.0, 1.25, 1.5]  # Multipliers of current capacity
        
        for capacity_multiplier in capacity_scenarios:
            available_capacity = resource_capacity.get("treatment_slots", 10) * capacity_multiplier
            
            try:
                # Create queueing model
                model = QueueingModel(daily_demand, service_rate, int(available_capacity))
                waiting_stats = model.waiting_time_distribution()
                
                results.append({
                    "strategy": strategy,
                    "capacity_multiplier": capacity_multiplier,
                    "available_capacity": available_capacity,
                    "daily_demand": daily_demand,
                    "utilization_rate": waiting_stats["utilization_rate"],
                    "mean_waiting_days": waiting_stats["mean_waiting_time"],
                    "median_waiting_days": waiting_stats["median_waiting_time"],
                    "p95_waiting_days": waiting_stats["p95_waiting_time"],
                    "probability_waiting": waiting_stats["probability_waiting"],
                    "bottleneck_indicator": "High" if waiting_stats["utilization_rate"] > 0.8 else 
                                          "Medium" if waiting_stats["utilization_rate"] > 0.6 else "Low"
                })
                
            except ValueError:
                # Unstable system
                results.append({
                    "strategy": strategy,
                    "capacity_multiplier": capacity_multiplier,
                    "available_capacity": available_capacity,
                    "daily_demand": daily_demand,
                    "utilization_rate": float('inf'),
                    "mean_waiting_days": float('inf'),
                    "median_waiting_days": float('inf'),
                    "p95_waiting_days": float('inf'),
                    "probability_waiting": 1.0,
                    "bottleneck_indicator": "Critical"
                })
    
    results_df = pd.DataFrame(results)
    
    # Create summary DataFrames
    waiting_times = results_df[["strategy", "capacity_multiplier", "mean_waiting_days", 
                               "median_waiting_days", "p95_waiting_days"]]
    
    utilization_rates = results_df[["strategy", "capacity_multiplier", "utilization_rate", 
                                   "probability_waiting", "bottleneck_indicator"]]
    
    # Bottleneck analysis
    bottleneck_analysis = results_df.groupby("strategy").agg({
        "utilization_rate": "max",
        "bottleneck_indicator": lambda x: x.iloc[0] if len(x) > 0 else "Unknown"
    }).reset_index()
    
    # Capacity requirements for acceptable waiting times
    capacity_requirements = results_df[results_df["mean_waiting_days"] <= 14].groupby("strategy").agg({
        "capacity_multiplier": "min",
        "available_capacity": "min"
    }).reset_index()
    
    # Queueing metrics summary
    queueing_metrics = results_df.groupby("strategy").agg({
        "utilization_rate": ["mean", "std", "min", "max"],
        "mean_waiting_days": ["mean", "std", "min", "max"],
        "probability_waiting": ["mean", "std"]
    }).round(3)
    queueing_metrics.columns = ["_".join(col).strip() for col in queueing_metrics.columns]
    
    return CapacityConstraintResult(
        waiting_times=waiting_times,
        utilization_rates=utilization_rates,
        bottleneck_analysis=bottleneck_analysis,
        capacity_requirements=capacity_requirements,
        queueing_metrics=queueing_metrics,
        perspective="health_system",
        jurisdiction=None
    )


def analyze_implementation_costs(
    treatment_volumes: pd.DataFrame,
    cost_parameters: Dict[str, Any],
    time_horizon: int = 5
) -> ImplementationCostResult:
    """
    Analyze implementation costs for treatment adoption.
    
    Args:
        treatment_volumes: DataFrame with expected treatment volumes
        cost_parameters: Dictionary of cost parameters
        time_horizon: Implementation time horizon in years
        
    Returns:
        Implementation cost analysis results
    """
    strategies = treatment_volumes["strategy"].unique()
    
    # Default cost parameters if not provided
    default_costs = {
        "startup_equipment": {"ECT": 50000, "KA-ECT": 75000, "IV-KA": 25000, "IN-EKA": 15000, 
                             "PO-PSI": 10000, "PO-KA": 5000, "rTMS": 100000, "UC+Li": 2000, "UC+AA": 2000, "Usual Care": 0},
        "training_per_staff": {"ECT": 5000, "KA-ECT": 7500, "IV-KA": 3000, "IN-EKA": 2000,
                              "PO-PSI": 1500, "PO-KA": 1000, "rTMS": 8000, "UC+Li": 500, "UC+AA": 500, "Usual Care": 0},
        "ongoing_supplies": {"ECT": 500, "KA-ECT": 750, "IV-KA": 200, "IN-EKA": 100,
                            "PO-PSI": 50, "PO-KA": 25, "rTMS": 1000, "UC+Li": 10, "UC+AA": 10, "Usual Care": 0},
        "monitoring_per_patient": {"ECT": 200, "KA-ECT": 300, "IV-KA": 150, "IN-EKA": 100,
                                  "PO-PSI": 75, "PO-KA": 50, "rTMS": 250, "UC+Li": 25, "UC+AA": 25, "Usual Care": 10},
        "adoption_outreach": 10000,  # One-time cost per strategy
        "staff_time_training": 40,   # Hours per staff member
        "staff_hourly_rate": 75      # Cost per hour
    }
    
    # Merge with provided parameters
    costs = {**default_costs, **cost_parameters}
    
    startup_costs = []
    operational_costs = []
    training_costs = []
    adoption_costs = []
    
    for strategy in strategies:
        strategy_volume = treatment_volumes[treatment_volumes["strategy"] == strategy]
        annual_patients = strategy_volume["annual_volume"].sum()
        
        # Startup costs
        equipment_cost = costs["startup_equipment"].get(strategy, 0)
        adoption_cost = costs["adoption_outreach"]
        
        startup_costs.append({
            "strategy": strategy,
            "equipment_cost": equipment_cost,
            "adoption_cost": adoption_cost,
            "total_startup": equipment_cost + adoption_cost
        })
        
        # Training costs
        staff_needed = max(1, annual_patients / 200)  # Assume 200 patients per staff
        training_hours = costs["staff_time_training"] * staff_needed
        training_cost = training_hours * costs["staff_hourly_rate"]
        
        training_costs.append({
            "strategy": strategy,
            "staff_needed": staff_needed,
            "training_hours": training_hours,
            "training_cost": training_cost
        })
        
        # Operational costs (annual)
        supplies_cost = costs["ongoing_supplies"].get(strategy, 0) * annual_patients
        monitoring_cost = costs["monitoring_per_patient"].get(strategy, 0) * annual_patients
        
        operational_costs.append({
            "strategy": strategy,
            "annual_patients": annual_patients,
            "supplies_cost": supplies_cost,
            "monitoring_cost": monitoring_cost,
            "total_operational": supplies_cost + monitoring_cost
        })
        
        # Adoption costs (first year only)
        adoption_costs.append({
            "strategy": strategy,
            "adoption_cost": adoption_cost,
            "adoption_rate_target": 0.7,  # 70% adoption target
            "marketing_cost": adoption_cost * 0.5
        })
    
    # Create DataFrames
    startup_df = pd.DataFrame(startup_costs)
    operational_df = pd.DataFrame(operational_costs)
    training_df = pd.DataFrame(training_costs)
    adoption_df = pd.DataFrame(adoption_costs)
    
    # Total costs with amortization
    total_costs = []
    cost_amortization = []
    breakeven_analysis = []
    
    for strategy in strategies:
        startup = startup_df[startup_df["strategy"] == strategy]["total_startup"].iloc[0]
        operational = operational_df[operational_df["strategy"] == strategy]["total_operational"].iloc[0]
        training = training_df[training_df["strategy"] == strategy]["training_cost"].iloc[0]
        
        # Amortization schedule (5-year straight line)
        annual_amortization = startup / time_horizon
        
        for year in range(1, time_horizon + 1):
            cost_amortization.append({
                "strategy": strategy,
                "year": year,
                "startup_amortization": annual_amortization,
                "operational_cost": operational,
                "training_cost": training if year == 1 else 0,
                "total_annual_cost": annual_amortization + operational + (training if year == 1 else 0)
            })
        
        # Total costs
        total_costs.append({
            "strategy": strategy,
            "total_startup": startup,
            "total_training": training,
            "annual_operational": operational,
            "total_5year_cost": startup + training + operational * time_horizon
        })
        
        # Breakeven analysis (simplified)
        # Assume each treatment generates some revenue
        revenue_per_patient = 2000  # Simplified assumption
        annual_revenue = operational_df[operational_df["strategy"] == strategy]["annual_patients"].iloc[0] * revenue_per_patient
        
        cumulative_cost = 0
        cumulative_revenue = 0
        breakeven_year = None
        
        for year in range(1, time_horizon + 1):
            cumulative_cost += annual_amortization + operational + (training if year == 1 else 0)
            cumulative_revenue += annual_revenue
            
            if breakeven_year is None and cumulative_revenue >= cumulative_cost:
                breakeven_year = year
        
        breakeven_analysis.append({
            "strategy": strategy,
            "annual_revenue": annual_revenue,
            "breakeven_year": breakeven_year or f">{time_horizon}",
            "profitability_ratio": annual_revenue / operational if operational > 0 else float('inf')
        })
    
    total_costs_df = pd.DataFrame(total_costs)
    cost_amortization_df = pd.DataFrame(cost_amortization)
    breakeven_df = pd.DataFrame(breakeven_analysis)
    
    return ImplementationCostResult(
        startup_costs=startup_df,
        operational_costs=operational_df,
        training_costs=training_df,
        adoption_costs=adoption_df,
        total_costs=total_costs_df,
        cost_amortization=cost_amortization_df,
        breakeven_analysis=breakeven_df,
        perspective="health_system",
        jurisdiction=None
    )