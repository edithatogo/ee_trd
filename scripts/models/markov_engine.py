"""
V4 Semi-Markov Model Engine

Implements time-dependent transitions with tunnel states for modeling waning effects and relapse hazards.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class MarkovState:
    """Definition of a Markov state."""
    
    name: str
    utility: float
    cost_per_cycle: float
    is_absorbing: bool = False


@dataclass
class TunnelState:
    """Tunnel state for time-dependent transitions."""
    
    base_state: str
    time_period: str  # e.g., "0-3m", "4-6m", "7-12m", ">12m"
    utility: float
    cost_per_cycle: float
    transition_probabilities: Dict[str, float]


@dataclass
class MarkovTrace:
    """Results from Markov model simulation."""
    
    state_occupancy: pd.DataFrame  # Proportion in each state over time
    costs: pd.DataFrame            # Costs accumulated over time
    qalys: pd.DataFrame            # QALYs accumulated over time
    total_cost: float
    total_qalys: float
    life_years: float


class SemiMarkovModel:
    """
    Semi-Markov model with time-dependent transitions.
    
    States: Depressed, PartialResponse, Remission, Relapse, Death
    Tunnel states for time-since-response to model waning effects
    """
    
    def __init__(
        self,
        states: List[MarkovState],
        tunnel_states: Optional[List[TunnelState]] = None,
        cycle_length: float = 1/12,  # Monthly cycles (1/12 year)
        discount_rate: float = 0.05
    ):
        """
        Initialize semi-Markov model.
        
        Args:
            states: List of Markov states
            tunnel_states: Optional list of tunnel states for time-dependency
            cycle_length: Length of each cycle in years
            discount_rate: Annual discount rate
        """
        self.states = {s.name: s for s in states}
        self.tunnel_states = tunnel_states or []
        self.cycle_length = cycle_length
        self.discount_rate = discount_rate
        
        # Create state name list
        self.state_names = list(self.states.keys())
        if self.tunnel_states:
            self.state_names.extend([f"{ts.base_state}_{ts.time_period}" for ts in self.tunnel_states])
    
    def create_transition_matrix(
        self,
        base_transitions: Dict[Tuple[str, str], float],
        cycle: int
    ) -> np.ndarray:
        """
        Create transition probability matrix for given cycle.
        
        Args:
            base_transitions: Base transition probabilities
            cycle: Current cycle number
        
        Returns:
            Transition probability matrix
        """
        n_states = len(self.state_names)
        matrix = np.zeros((n_states, n_states))
        
        # Fill in base transitions
        for (from_state, to_state), prob in base_transitions.items():
            if from_state in self.state_names and to_state in self.state_names:
                i = self.state_names.index(from_state)
                j = self.state_names.index(to_state)
                matrix[i, j] = prob
        
        # Ensure rows sum to 1
        for i in range(n_states):
            row_sum = matrix[i, :].sum()
            if row_sum > 0 and not np.isclose(row_sum, 1.0):
                matrix[i, :] /= row_sum
            elif row_sum == 0:
                # Stay in same state if no transitions defined
                matrix[i, i] = 1.0
        
        return matrix
    
    def simulate(
        self,
        initial_state: str,
        n_cycles: int,
        transition_probabilities: Dict[Tuple[str, str], float],
        time_dependent_transitions: Optional[Dict[int, Dict[Tuple[str, str], float]]] = None
    ) -> MarkovTrace:
        """
        Simulate Markov model.
        
        Args:
            initial_state: Starting state
            n_cycles: Number of cycles to simulate
            transition_probabilities: Base transition probabilities
            time_dependent_transitions: Optional cycle-specific transitions
        
        Returns:
            MarkovTrace with simulation results
        """
        n_states = len(self.state_names)
        
        # Initialize state occupancy
        state_occupancy = np.zeros((n_cycles + 1, n_states))
        initial_idx = self.state_names.index(initial_state)
        state_occupancy[0, initial_idx] = 1.0
        
        # Track costs and QALYs
        costs = np.zeros(n_cycles + 1)
        qalys = np.zeros(n_cycles + 1)
        
        # Simulate each cycle
        for cycle in range(n_cycles):
            # Get transition matrix for this cycle
            if time_dependent_transitions and cycle in time_dependent_transitions:
                trans_probs = time_dependent_transitions[cycle]
            else:
                trans_probs = transition_probabilities
            
            trans_matrix = self.create_transition_matrix(trans_probs, cycle)
            
            # Update state occupancy
            state_occupancy[cycle + 1, :] = state_occupancy[cycle, :] @ trans_matrix
            
            # Calculate costs and QALYs for this cycle
            discount_factor = 1 / ((1 + self.discount_rate) ** (cycle * self.cycle_length))
            
            for i, state_name in enumerate(self.state_names):
                occupancy = state_occupancy[cycle + 1, i]
                
                if state_name in self.states:
                    state = self.states[state_name]
                    costs[cycle + 1] += occupancy * state.cost_per_cycle * discount_factor
                    qalys[cycle + 1] += occupancy * state.utility * self.cycle_length * discount_factor
        
        # Create results dataframes
        state_occupancy_df = pd.DataFrame(
            state_occupancy,
            columns=self.state_names
        )
        state_occupancy_df['cycle'] = range(n_cycles + 1)
        
        costs_df = pd.DataFrame({
            'cycle': range(n_cycles + 1),
            'cost': costs,
            'cumulative_cost': np.cumsum(costs)
        })
        
        qalys_df = pd.DataFrame({
            'cycle': range(n_cycles + 1),
            'qalys': qalys,
            'cumulative_qalys': np.cumsum(qalys)
        })
        
        return MarkovTrace(
            state_occupancy=state_occupancy_df,
            costs=costs_df,
            qalys=qalys_df,
            total_cost=costs.sum(),
            total_qalys=qalys.sum(),
            life_years=n_cycles * self.cycle_length
        )


def create_trd_model(
    treatment_efficacy: float,
    relapse_rate: float,
    mortality_rate: float = 0.001,
    cycle_length: float = 1/12,
    discount_rate: float = 0.05
) -> SemiMarkovModel:
    """
    Create semi-Markov model for treatment-resistant depression.
    
    States:
    - Depressed: Active TRD symptoms
    - PartialResponse: Some improvement but not remission
    - Remission: Treatment response with sustained improvement
    - Relapse: Return to depressed state after remission
    - Death: Absorbing state
    
    Args:
        treatment_efficacy: Probability of achieving remission
        relapse_rate: Monthly probability of relapse from remission
        mortality_rate: Monthly mortality rate
        cycle_length: Cycle length in years
        discount_rate: Annual discount rate
    
    Returns:
        Configured SemiMarkovModel
    """
    # Define states with utilities and costs
    states = [
        MarkovState(
            name="Depressed",
            utility=0.45,  # Low utility in depressed state
            cost_per_cycle=500  # Monthly healthcare costs
        ),
        MarkovState(
            name="PartialResponse",
            utility=0.65,  # Moderate utility
            cost_per_cycle=400
        ),
        MarkovState(
            name="Remission",
            utility=0.85,  # High utility in remission
            cost_per_cycle=200  # Lower costs in remission
        ),
        MarkovState(
            name="Relapse",
            utility=0.50,  # Similar to depressed
            cost_per_cycle=600  # Higher costs due to relapse management
        ),
        MarkovState(
            name="Death",
            utility=0.0,
            cost_per_cycle=0,
            is_absorbing=True
        )
    ]
    
    # Create tunnel states for time-since-remission
    # This allows modeling of waning treatment effects
    tunnel_periods = ["0-3m", "4-6m", "7-12m", ">12m"]
    tunnel_states = []
    
    for period in tunnel_periods:
        # Relapse risk increases over time
        if period == "0-3m":
            period_relapse_rate = relapse_rate * 0.5
        elif period == "4-6m":
            period_relapse_rate = relapse_rate * 0.75
        elif period == "7-12m":
            period_relapse_rate = relapse_rate
        else:  # >12m
            period_relapse_rate = relapse_rate * 1.25
        
        tunnel_states.append(TunnelState(
            base_state="Remission",
            time_period=period,
            utility=0.85,
            cost_per_cycle=200,
            transition_probabilities={
                "Remission": 1 - period_relapse_rate - mortality_rate,
                "Relapse": period_relapse_rate,
                "Death": mortality_rate
            }
        ))
    
    return SemiMarkovModel(
        states=states,
        tunnel_states=tunnel_states,
        cycle_length=cycle_length,
        discount_rate=discount_rate
    )


def run_markov_analysis(
    model: SemiMarkovModel,
    initial_state: str,
    time_horizon_years: int,
    transition_probabilities: Dict[Tuple[str, str], float]
) -> MarkovTrace:
    """
    Run Markov model analysis.
    
    Args:
        model: SemiMarkovModel instance
        initial_state: Starting state
        time_horizon_years: Time horizon in years
        transition_probabilities: Transition probabilities
    
    Returns:
        MarkovTrace with results
    """
    n_cycles = int(time_horizon_years / model.cycle_length)
    
    return model.simulate(
        initial_state=initial_state,
        n_cycles=n_cycles,
        transition_probabilities=transition_probabilities
    )
