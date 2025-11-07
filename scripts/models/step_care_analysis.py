#!/usr/bin/env python3
"""
Step-care pathway analysis for TRD economic model.

Calculates expected costs and QALYs for step-care treatment sequences
where patients progress through treatments based on response rates.
"""

import pandas as pd
from pathlib import Path
import yaml

# Treatment response rates (remission probabilities)
TREATMENT_RESPONSES = {
    "Usual care": 0.20,  # Base pharmacotherapy remission rate
    "rTMS": 0.35,        # rTMS remission rate
    "IV-KA": 0.45,       # IV ketamine remission rate (mock)
    "PO-KA": 0.40,       # Oral ketamine remission rate
    "ECT": 0.60          # ECT remission rate (mock)
}

# Mock cost and effect data for missing strategies
MOCK_STRATEGY_DATA = {
    "IV-KA": {"cost": 5000, "effect": 2.3},
    "ECT": {"cost": 8000, "effect": 2.5}
}

def calculate_sequential_icers(sequence, psa_data_path):
    """
    Calculate sequential ICERs for a step-care sequence.

    Returns list of ICERs comparing each step to the previous.
    """
    psa_df = pd.read_csv(psa_data_path)
    strategy_means = psa_df.groupby('strategy')[['cost', 'effect']].mean()

    icers = []
    for i in range(1, len(sequence)):
        prev_treatment = sequence[i-1]
        current_treatment = sequence[i]

        # Get outcomes
        if prev_treatment in strategy_means.index:
            prev_cost = strategy_means.loc[prev_treatment, 'cost']
            prev_effect = strategy_means.loc[prev_treatment, 'effect']
        elif prev_treatment in MOCK_STRATEGY_DATA:
            prev_cost = MOCK_STRATEGY_DATA[prev_treatment]['cost']
            prev_effect = MOCK_STRATEGY_DATA[prev_treatment]['effect']
        else:
            continue

        if current_treatment in strategy_means.index:
            curr_cost = strategy_means.loc[current_treatment, 'cost']
            curr_effect = strategy_means.loc[current_treatment, 'effect']
        elif current_treatment in MOCK_STRATEGY_DATA:
            curr_cost = MOCK_STRATEGY_DATA[current_treatment]['cost']
            curr_effect = MOCK_STRATEGY_DATA[current_treatment]['effect']
        else:
            continue

        # Calculate ICER
        delta_cost = curr_cost - prev_cost
        delta_effect = curr_effect - prev_effect

        if delta_effect > 0:
            icer = delta_cost / delta_effect
            icers.append(icer)
        else:
            icers.append(float('inf'))  # Dominated

    return icers

def calculate_step_care_outcomes(sequence, psa_data_path, clinical_data_path):
    """
    Calculate expected outcomes for a step-care sequence.

    Args:
        sequence: List of treatment names in order
        psa_data_path: Path to PSA data CSV
        clinical_data_path: Path to clinical inputs CSV

    Returns:
        dict: Expected cost and QALYs for the sequence
    """

    # Load PSA data
    psa_df = pd.read_csv(psa_data_path)

    # For simplicity, use mean values across draws for each strategy
    strategy_means = psa_df.groupby('strategy')[['cost', 'effect']].mean()

    results = {'cost': 0.0, 'effect': 0.0}
    remaining_patients = 1.0

    for i, treatment in enumerate(sequence):
        # Get treatment outcomes
        if treatment in strategy_means.index:
            treatment_cost = strategy_means.loc[treatment, 'cost']
            treatment_effect = strategy_means.loc[treatment, 'effect']
        elif treatment in MOCK_STRATEGY_DATA:
            treatment_cost = MOCK_STRATEGY_DATA[treatment]['cost']
            treatment_effect = MOCK_STRATEGY_DATA[treatment]['effect']
        else:
            print(f"Warning: {treatment} not found in PSA data or mock data, skipping")
            continue

        # Get response rate for this treatment
        response_rate = TREATMENT_RESPONSES.get(treatment, 0.0)

        # Calculate outcomes for patients receiving this treatment
        # (remaining_patients * (1 - response_rate) get this treatment)
        patients_receiving = remaining_patients * (1 - response_rate) if i > 0 else remaining_patients

        results['cost'] += patients_receiving * treatment_cost
        results['effect'] += patients_receiving * treatment_effect

        # Update remaining patients (those who didn't respond)
        remaining_patients *= (1 - response_rate)

    return results

def main():
    # Load step-care sequences from config
    config_path = Path(__file__).parent.parent / "config" / "strategies.yml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    sequences = config.get('step_care_sequences', {})

    # PSA data path
    psa_path = Path(__file__).parent.parent / "build" / "smoke_oral_ketamine" / "psa_extended.csv"

    results = {}
    for seq_name, seq_treatments in sequences.items():
        outcomes = calculate_step_care_outcomes(seq_treatments, psa_path, None)
        icers = calculate_sequential_icers(seq_treatments, psa_path)

        results[seq_name] = {
            'cost': outcomes['cost'],
            'effect': outcomes['effect'],
            'icers': icers
        }

        print(f"{seq_name}:")
        print(".2f")
        print(".3f")
        print(f"Sequential ICERs: {[f'{icer:,.0f}' if icer != float('inf') else 'Dominated' for icer in icers]}")
        print()

    # Save results
    results_df = pd.DataFrame.from_dict({k: {**v, 'icers': str(v['icers'])} for k, v in results.items()}, orient='index')
    output_path = Path(__file__).parent.parent / "results" / "step_care_analysis.csv"
    output_path.parent.mkdir(exist_ok=True)
    results_df.to_csv(output_path)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()