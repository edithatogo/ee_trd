#!/usr/bin/env python3
"""Add ICER column to CEA deterministic results."""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)


def add_icer_column(cea_file):
    """Add ICER column to CEA results."""
    df = pd.read_csv(cea_file)
    
    # Calculate ICER
    if 'incremental_cost' in df.columns and 'incremental_effect' in df.columns:
        # Use existing incremental columns
        df['icer'] = df['incremental_cost'] / df['incremental_effect']
        # Handle division by zero
        df.loc[df['incremental_effect'] == 0, 'icer'] = np.inf
        df.loc[(df['incremental_effect'] == 0) & (df['incremental_cost'] == 0), 'icer'] = 0
    else:
        # Calculate from base strategy (UC)
        if 'UC' in df['strategy'].values:
            base_cost = df[df['strategy'] == 'UC']['cost'].iloc[0]
            base_effect = df[df['strategy'] == 'UC']['effect'].iloc[0]
        else:
            # Use first strategy as base
            base_cost = df['cost'].iloc[0]
            base_effect = df['effect'].iloc[0]
        
        df['incremental_cost'] = df['cost'] - base_cost
        df['incremental_effect'] = df['effect'] - base_effect
        df['icer'] = df['incremental_cost'] / df['incremental_effect']
        
        # Handle division by zero and negative values
        df.loc[df['incremental_effect'] == 0, 'icer'] = np.inf
        df.loc[(df['incremental_effect'] == 0) & (df['incremental_cost'] == 0), 'icer'] = 0
        df.loc[df['incremental_effect'] < 0, 'icer'] = -df.loc[df['incremental_effect'] < 0, 'icer']
    
    df.to_csv(cea_file, index=False)
    print(f"✓ Added ICER to {cea_file}")


def main():
    """Add ICER to all CEA files."""
    print("=" * 70)
    print("Adding ICER Column to CEA Results")
    print("=" * 70)
    print()
    
    # Process all perspectives
    base_dir = Path('outputs_v4/run_latest')
    perspectives = [
        ('AU', 'healthcare'),
        ('AU', 'societal'),
        ('NZ', 'healthcare'),
        ('NZ', 'societal'),
    ]
    
    success_count = 0
    for jurisdiction, perspective in perspectives:
        cea_file = base_dir / jurisdiction / perspective / 'cea_deterministic.csv'
        if cea_file.exists():
            try:
                add_icer_column(cea_file)
                success_count += 1
            except Exception as e:
                print(f"✗ Error processing {cea_file}: {e}")
        else:
            print(f"✗ File not found: {cea_file}")
    
    print()
    print("=" * 70)
    print(f"✓ ICER added to {success_count}/{len(perspectives)} CEA files")
    print("=" * 70)
    
    return 0 if success_count == len(perspectives) else 1


if __name__ == '__main__':
    exit(main())
