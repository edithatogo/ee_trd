#!/usr/bin/env python3
"""
Markov Model for Treatment-Resistant Depression
Demonstrates a basic Markov model structure for TRD with 4 health states.
"""

import numpy as np
import pandas as pd
from pathlib import Path

class DepressionMarkovModel:
    """Markov model for treatment-resistant depression."""

    def __init__(self, country="AU"):
        self.country = country
        self.cycle_length = 1  # month
        self.time_horizon = 120  # 10 years in months
        self.discount_rate = 0.05  # 5% annual discount rate

        # Health states
        self.states = ['Initial_Depression', 'Remission', 'Partial_Remission', 'Severe_Depression']

        # State utilities (QALYs per month)
        self.utilities = {
            'Initial_Depression': 0.57,  # Depressed utility
            'Remission': 0.81,           # Remission utility
            'Partial_Remission': 0.69,   # Partial remission utility
            'Severe_Depression': 0.57    # Severe depression utility
        }

        # State costs (monthly)
        self.healthcare_costs = {
            'Initial_Depression': 500,   # Intensive treatment
            'Remission': 50,             # Maintenance/follow-up
            'Partial_Remission': 200,    # Moderate treatment
            'Severe_Depression': 800     # Intensive treatment
        }

        # Societal costs (monthly productivity losses)
        self.productivity_costs = {
            'Initial_Depression': 2000,
            'Remission': 0,
            'Partial_Remission': 1000,
            'Severe_Depression': 2000
        }

    def get_transition_matrix(self, treatment):
        """Get transition probability matrix for a given treatment."""

        # Base transition probabilities (monthly)
        if treatment == "ECT":
            transitions = {
                'Initial_Depression': {'Remission': 0.55, 'Partial_Remission': 0.30, 'Severe_Depression': 0.15},
                'Remission': {'Remission': 0.85, 'Partial_Remission': 0.10, 'Severe_Depression': 0.05},
                'Partial_Remission': {'Remission': 0.20, 'Partial_Remission': 0.70, 'Severe_Depression': 0.10},
                'Severe_Depression': {'Remission': 0.05, 'Partial_Remission': 0.15, 'Severe_Depression': 0.80}
            }
        elif treatment == "Ketamine":
            transitions = {
                'Initial_Depression': {'Remission': 0.45, 'Partial_Remission': 0.35, 'Severe_Depression': 0.20},
                'Remission': {'Remission': 0.80, 'Partial_Remission': 0.15, 'Severe_Depression': 0.05},
                'Partial_Remission': {'Remission': 0.25, 'Partial_Remission': 0.65, 'Severe_Depression': 0.10},
                'Severe_Depression': {'Remission': 0.03, 'Partial_Remission': 0.12, 'Severe_Depression': 0.85}
            }
        elif treatment == "Psilocybin":
            transitions = {
                'Initial_Depression': {'Remission': 0.40, 'Partial_Remission': 0.40, 'Severe_Depression': 0.20},
                'Remission': {'Remission': 0.90, 'Partial_Remission': 0.08, 'Severe_Depression': 0.02},  # More sustained
                'Partial_Remission': {'Remission': 0.30, 'Partial_Remission': 0.60, 'Severe_Depression': 0.10},
                'Severe_Depression': {'Remission': 0.04, 'Partial_Remission': 0.16, 'Severe_Depression': 0.80}
            }
        else:  # No treatment
            transitions = {
                'Initial_Depression': {'Remission': 0.10, 'Partial_Remission': 0.30, 'Severe_Depression': 0.60},
                'Remission': {'Remission': 0.70, 'Partial_Remission': 0.20, 'Severe_Depression': 0.10},
                'Partial_Remission': {'Remission': 0.10, 'Partial_Remission': 0.60, 'Severe_Depression': 0.30},
                'Severe_Depression': {'Remission': 0.02, 'Partial_Remission': 0.08, 'Severe_Depression': 0.90}
            }

        # Convert to matrix
        n_states = len(self.states)
        matrix = np.zeros((n_states, n_states))

        for i, from_state in enumerate(self.states):
            for j, to_state in enumerate(self.states):
                if from_state in transitions and to_state in transitions[from_state]:
                    matrix[i, j] = transitions[from_state][to_state]

        return matrix

    def run_markov_model(self, treatment, initial_state='Initial_Depression'):
        """Run the Markov model simulation."""

        # Get transition matrix
        transition_matrix = self.get_transition_matrix(treatment)

        # Initialize state vector (cohort starts in initial depression)
        state_vector = np.zeros(len(self.states))
        initial_idx = self.states.index(initial_state)
        state_vector[initial_idx] = 1.0

        # Track outcomes
        total_costs = 0
        total_qalys = 0
        state_occupancy = {state: [] for state in self.states}

        for cycle in range(self.time_horizon):
            # Record state occupancy
            for i, state in enumerate(self.states):
                state_occupancy[state].append(state_vector[i])

            # Calculate QALYs for this cycle
            cycle_qaly = 0
            cycle_cost = 0

            for i, state in enumerate(self.states):
                proportion = state_vector[i]

                # QALYs
                utility = self.utilities[state]
                cycle_qaly += proportion * utility * (self.cycle_length / 12)  # Convert to years

                # Costs
                healthcare_cost = self.healthcare_costs[state] * self.cycle_length
                productivity_cost = self.productivity_costs[state] * self.cycle_length
                total_cycle_cost = healthcare_cost + productivity_cost
                cycle_cost += proportion * total_cycle_cost

            # Apply discounting
            discount_factor = (1 + self.discount_rate) ** -(cycle / 12)  # Annual discounting
            total_qalys += cycle_qaly * discount_factor
            total_costs += cycle_cost * discount_factor

            # Transition to next state
            state_vector = np.dot(state_vector, transition_matrix)

        return {
            'treatment': treatment,
            'total_costs': total_costs,
            'total_qalys': total_qalys,
            'state_occupancy': state_occupancy
        }

def main():
    """Run Markov model comparison."""
    print("Markov Model Analysis for Treatment-Resistant Depression")
    print("=" * 60)

    treatments = ['ECT', 'Ketamine', 'Psilocybin']
    countries = ['AU', 'NZ']

    results = []

    for country in countries:
        print(f"\n{country} Results:")
        print("-" * 30)

        model = DepressionMarkovModel(country)

        for treatment in treatments:
            result = model.run_markov_model(treatment)
            results.append({
                'Country': country,
                'Treatment': treatment,
                'Total_Costs': result['total_costs'],
                'Total_QALYs': result['total_qalys']
            })

            print(f"{treatment}:")
            print(".2f")
            print(".3f")

            # Show final state distribution
            final_states = {state: occupancy[-1] for state, occupancy in result['state_occupancy'].items()}
            print(f"  Final state distribution: {final_states}")

    # Save results
    results_df = pd.DataFrame(results)
    output_file = Path('/Users/doughnut/Library/CloudStorage/OneDrive-NSWHealthDepartment/Project - EE - IV Ketamine vs ECT/markov_model_results.csv')
    results_df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()