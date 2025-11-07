#!/usr/bin/env python3
"""
Generate PSA data for step-care sequences by combining component therapies.

This script takes the existing PSA data and creates new rows for step-care sequences
by computing weighted averages of the component therapies defined in the config.
"""

import pandas as pd
import yaml
from pathlib import Path
import argparse
from typing import Dict, List

def load_config(config_path: Path) -> Dict:
    """Load strategy configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_psa_data(psa_path: Path) -> pd.DataFrame:
    """Load PSA data."""
    return pd.read_csv(psa_path)

def calculate_step_care_values(
    psa_data: pd.DataFrame, 
    sequence: List[str], 
    sequence_name: str,
    draw: int,
    perspective: str
) -> Dict:
    """
    Calculate cost and effect for a step-care sequence.
    
    For step-care, we sum the costs and take a weighted average of effects
    based on the likelihood of progressing through each step.
    """
    # Get data for this draw and perspective
    draw_data = psa_data[
        (psa_data['draw'] == draw) & 
        (psa_data['perspective'] == perspective)
    ]
    
    total_cost = 0
    total_effect = 0
    
    # Define progression probabilities (these could be parameterized)
    # Assume 50% progress from step 1->2, 40% from 2->3, 30% from 3->4
    progression_probs = [1.0, 0.5, 0.4, 0.3]  # Everyone starts at step 1
    
    for i, strategy in enumerate(sequence):
        # Map strategy names (handle naming inconsistencies)
        strategy_mapped = strategy
        if strategy == "Usual Care":
            strategy_mapped = "Usual care"  # Match PSA data naming
        
        strategy_data = draw_data[draw_data['strategy'] == strategy_mapped]
        
        if strategy_data.empty:
            print(f"Warning: No data found for strategy '{strategy_mapped}' in draw {draw}")
            continue
            
        # Probability of reaching this step
        prob = progression_probs[min(i, len(progression_probs)-1)]
        
        # Add costs (everyone who reaches this step incurs the cost)
        total_cost += strategy_data['cost'].iloc[0] * prob
        
        # For effects, we take the last strategy's effect (final outcome)
        if i == len(sequence) - 1:
            total_effect = strategy_data['effect'].iloc[0]
    
    return {
        'draw': draw,
        'strategy': sequence_name,
        'cost': total_cost,
        'effect': total_effect,
        'perspective': perspective
    }

def generate_step_care_psa_data(
    psa_data: pd.DataFrame,
    config: Dict,
    output_path: Path
) -> pd.DataFrame:
    """Generate PSA data including step-care sequences."""
    
    # Start with existing data
    extended_data = psa_data.copy()
    
    # Fix strategy naming inconsistency
    extended_data['strategy'] = extended_data['strategy'].replace('Usual care', 'Usual Care')
    
    step_care_sequences = config.get('step_care_sequences', {})
    
    new_rows = []
    
    # Get unique draws and perspectives
    unique_draws = sorted(psa_data['draw'].unique())
    unique_perspectives = psa_data['perspective'].unique()
    
    print(f"Generating step-care data for {len(unique_draws)} draws across {len(unique_perspectives)} perspectives...")
    
    for sequence_name, sequence in step_care_sequences.items():
        print(f"Processing: {sequence_name}")
        print(f"  Sequence: {' → '.join(sequence)}")
        
        for perspective in unique_perspectives:
            for draw in unique_draws:
                step_care_values = calculate_step_care_values(
                    psa_data, sequence, sequence_name, draw, perspective
                )
                new_rows.append(step_care_values)
    
    # Add new rows to the dataset
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        extended_data = pd.concat([extended_data, new_df], ignore_index=True)
    
    # Sort by draw, then strategy
    extended_data = extended_data.sort_values(['draw', 'strategy', 'perspective']).reset_index(drop=True)
    
    # Save extended data
    extended_data.to_csv(output_path, index=False)
    
    print(f"\nExtended PSA data saved to: {output_path}")
    print(f"Original strategies: {len(psa_data['strategy'].unique())}")
    print(f"Extended strategies: {len(extended_data['strategy'].unique())}")
    print(f"Total rows: {len(extended_data)}")
    
    return extended_data

def main():
    parser = argparse.ArgumentParser(description="Generate step-care PSA data")
    parser.add_argument('--psa', type=str, required=True, help='Input PSA CSV file')
    parser.add_argument('--config', type=str, required=True, help='Strategy config YAML file')
    parser.add_argument('--output', type=str, required=True, help='Output PSA CSV file')
    
    args = parser.parse_args()
    
    psa_path = Path(args.psa)
    config_path = Path(args.config)
    output_path = Path(args.output)
    
    # Load data
    print(f"Loading PSA data from: {psa_path}")
    psa_data = load_psa_data(psa_path)
    
    print(f"Loading config from: {config_path}")
    config = load_config(config_path)
    
    # Generate extended PSA data
    extended_data = generate_step_care_psa_data(psa_data, config, output_path)
    
    print("\n✅ Step-care PSA data generation complete!")
    
    # Show strategy summary
    print("\nStrategy summary:")
    strategy_counts = extended_data.groupby('strategy').size()
    for strategy, count in strategy_counts.items():
        print(f"  {strategy}: {count} rows")

if __name__ == "__main__":
    main()