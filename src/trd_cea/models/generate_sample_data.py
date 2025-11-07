#!/usr/bin/env python3
"""
Generate sample PSA data for V4 testing and output generation.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from trd_cea.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# V4 therapy abbreviations
V4_STRATEGIES = [
    'UC',      # Usual Care
    'ECT',     # Standard ECT
    'KA-ECT',  # Ketamine-Assisted ECT
    'IV-KA',   # Intravenous Ketamine
    'IN-EKA',  # Intranasal Esketamine
    'PO-PSI',  # Oral Psilocybin
    'PO-KA',   # Oral Ketamine
    'rTMS',    # rTMS
    'UC+Li',   # Usual Care + Lithium
    'UC+AA',   # Usual Care + Antipsychotic
]

# Base costs and effects (approximate from literature)
BASE_PARAMS = {
    'UC': {'cost': 5000, 'effect': 3.0, 'cost_sd': 1000, 'effect_sd': 0.5},
    'ECT': {'cost': 15000, 'effect': 6.5, 'cost_sd': 3000, 'effect_sd': 0.8},
    'KA-ECT': {'cost': 18000, 'effect': 7.0, 'cost_sd': 3500, 'effect_sd': 0.9},
    'IV-KA': {'cost': 12000, 'effect': 5.5, 'cost_sd': 2500, 'effect_sd': 0.7},
    'IN-EKA': {'cost': 20000, 'effect': 5.0, 'cost_sd': 4000, 'effect_sd': 0.6},
    'PO-PSI': {'cost': 25000, 'effect': 6.0, 'cost_sd': 5000, 'effect_sd': 0.8},
    'PO-KA': {'cost': 8000, 'effect': 4.5, 'cost_sd': 1500, 'effect_sd': 0.6},
    'rTMS': {'cost': 10000, 'effect': 4.0, 'cost_sd': 2000, 'effect_sd': 0.5},
    'UC+Li': {'cost': 6000, 'effect': 3.5, 'cost_sd': 1200, 'effect_sd': 0.5},
    'UC+AA': {'cost': 7000, 'effect': 3.2, 'cost_sd': 1400, 'effect_sd': 0.5},
}


def generate_psa_data(
    n_draws=1000,
    strategies=None,
    perspective='healthcare',
    jurisdiction='AU',
    seed=42
):
    """
    Generate PSA data with V4 structure.
    
    Args:
        n_draws: Number of PSA iterations
        strategies: List of strategies (default: all V4 strategies)
        perspective: Perspective name
        jurisdiction: Jurisdiction code
        seed: Random seed
    
    Returns:
        DataFrame with PSA data
    """
    if strategies is None:
        strategies = V4_STRATEGIES
    
    np.random.seed(seed)
    
    data = []
    for draw in range(n_draws):
        for strategy in strategies:
            params = BASE_PARAMS[strategy]
            
            # Generate random costs and effects
            cost = np.random.normal(params['cost'], params['cost_sd'])
            effect = np.random.normal(params['effect'], params['effect_sd'])
            
            # Ensure non-negative
            cost = max(0, cost)
            effect = max(0, effect)
            
            data.append({
                'draw': draw,
                'strategy': strategy,
                'cost': cost,
                'effect': effect,
                'perspective': perspective,
                'jurisdiction': jurisdiction,
            })
    
    return pd.DataFrame(data)


def main():
    """Generate sample datasets for testing."""
    # Set up logging using centralized infrastructure
    # Logger already initialized at module level above

    logger.info("=" * 60)
    logger.info("Generating V4 Sample PSA Data...")
    logger.info("=" * 60)

    output_dir = Path('data/sample')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate datasets for different perspectives and jurisdictions
    configs = [
        ('healthcare', 'AU', 1000),
        ('healthcare', 'NZ', 1000),
        ('societal', 'AU', 1000),
        ('societal', 'NZ', 1000),
    ]

    for perspective, jurisdiction, n_draws in configs:
        logger.info(f"Generating: {jurisdiction} - {perspective}")

        # Generate data
        df = generate_psa_data(
            n_draws=n_draws,
            perspective=perspective,
            jurisdiction=jurisdiction
        )

        # Log data summary
        logger.info(f"  Generated data shape: {df.shape}")
        logger.info(f"  Strategies: {sorted(df['strategy'].unique())}")
        logger.info(f"  Mean cost: ${df['cost'].mean():,.0f}")
        logger.info(f"  Mean effect: {df['effect'].mean():.2f} QALYs")

        # Save to CSV
        filename = f'psa_sample_{jurisdiction}_{perspective}.csv'
        output_path = output_dir / filename
        df.to_csv(output_path, index=False)

        logger.info(f"  ✓ Created: {filename}")
        logger.info(f"  ✓ Shape: {df.shape}")
        logger.info(f"  ✓ Strategies: {df['strategy'].nunique()}")
        logger.info(f"  ✓ Draws: {df['draw'].nunique()}")

    # Generate a combined dataset
    logger.info("Generating: Combined dataset")
    df_combined = pd.concat([
        generate_psa_data(n_draws=1000, perspective='healthcare', jurisdiction='AU'),
        generate_psa_data(n_draws=1000, perspective='healthcare', jurisdiction='NZ'),
    ])

    # Log combined data summary
    logger.info(f"  Combined data shape: {df_combined.shape}")
    logger.info(f"  Jurisdictions included: {sorted(df_combined['jurisdiction'].unique())}")

    output_path = output_dir / 'psa_sample_combined.csv'
    df_combined.to_csv(output_path, index=False)
    logger.info("  ✓ Created: psa_sample_combined.csv")
    logger.info(f"  ✓ Shape: {df_combined.shape}")

    logger.info("=" * 60)
    logger.info("✓ Sample data generation complete!")
    logger.info(f"✓ Output directory: {output_dir}")
    logger.info(f"✓ Files created: {len(list(output_dir.glob('*.csv')))}")


if __name__ == '__main__':
    main()
