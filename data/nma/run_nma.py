#!/usr/bin/env python3
"""
Run Bayesian Network Meta-Analysis for TRD Treatments

This script executes the complete NMA pipeline:
1. Load data and configuration
2. Fit Bayesian model
3. Generate diagnostics
4. Export posterior draws for PSA
"""

import sys
import yaml
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from data.nma.nma_model import create_nma_model, fit_nma_model, generate_posterior_draws, plot_nma_results
from data.nma.nma_data import NMA_DATA

def load_config():
    """Load NMA configuration."""
    config_path = Path(__file__).parent / 'nma_config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    """Run the complete NMA analysis."""
    print("TRD Bayesian Network Meta-Analysis")
    print("=" * 40)

    # Load configuration
    config = load_config()
    print(f"Configuration loaded: {len(config['treatments'])} treatments")

    # Set random seed
    np.random.seed(config['random_seed'])

    # Prepare data
    print(f"Data loaded: {len(NMA_DATA)} study arms")
    print(f"Treatments: {sorted(NMA_DATA['treatment'].unique())}")
    print(f"Outcomes: {sorted(NMA_DATA['outcome'].unique())}")

    # Filter to response outcome for primary analysis
    response_data = NMA_DATA[NMA_DATA['outcome'] == 'response'].copy()
    print(f"Response data: {len(response_data)} study arms")

    # Create and fit model
    print("\nFitting Bayesian NMA model...")
    model = create_nma_model(response_data)

    trace = fit_nma_model(
        model,
        draws=config['n_draws'],
        tune=config['n_tune'],
        chains=config['n_chains']
    )

    print("Model fitting complete!")

    # Generate posterior draws for PSA
    print("\nGenerating posterior draws for PSA...")
    posterior_draws = generate_posterior_draws(trace, n_draws=1000)

    # Save results
    output_dir = Path(__file__).parent
    output_file = output_dir / 'nma_posterior_draws.parquet'
    posterior_draws.to_parquet(output_file)
    print(f"Posterior draws saved to: {output_file}")
    print(f"Shape: {posterior_draws.shape}")

    # Create diagnostics
    print("\nCreating diagnostic plots...")
    fig = plot_nma_results(trace, response_data)
    plot_file = output_dir / 'nma_diagnostics.png'
    fig.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"Diagnostic plots saved to: {plot_file}")

    # Print summary statistics
    print("\nNMA Results Summary:")
    print("-" * 30)

    # Treatment effects relative to ECT
    print("Treatment Effects (log OR vs ECT):")
    for treatment in config['treatments'][1:]:  # Skip ECT (reference)
        if f'{treatment}_logOR' in posterior_draws.columns:
            samples = posterior_draws[f'{treatment}_logOR'].values
            _mean_or = np.mean(samples)
            _hdi = np.percentile(samples, [2.5, 97.5])
            print(".3f")

    print("\nAbsolute Response Probabilities:")
    for treatment in config['treatments']:
        if f'{treatment}_prob' in posterior_draws.columns:
            samples = posterior_draws[f'{treatment}_prob'].values
            _mean_prob = np.mean(samples)
            _hdi = np.percentile(samples, [2.5, 97.5])
            print(".3f")

    print(f"\nNMA analysis complete! Results saved to {output_dir}")

if __name__ == '__main__':
    main()