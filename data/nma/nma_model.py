"""
Bayesian Network Meta-Analysis for TRD Treatments

This module implements a Bayesian NMA comparing:
- ECT (Electroconvulsive Therapy)
- IV-KA (IV Ketamine)
- IN-EKA (Intranasal Esketamine)
- PO-PSI (Oral Psilocybin)
- rTMS (Repetitive Transcranial Magnetic Stimulation)
- PHARM (Pharmacological augmentation)

Outcomes: Response rates and remission rates from clinical trials.
"""

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle

# Set random seed for reproducibility
np.random.seed(42)

# Treatment codes
TREATMENTS = {
    'ECT': 0,
    'IV_KA': 1,
    'IN_EKA': 2,
    'PO_PSI': 3,
    'rTMS': 4,
    'PHARM': 5
}

# Synthetic NMA data (based on typical TRD trial results)
# In practice, this would be loaded from actual clinical trial data
NMA_DATA = pd.DataFrame({
    'study': ['Study_A', 'Study_A', 'Study_B', 'Study_B', 'Study_C', 'Study_C',
              'Study_D', 'Study_D', 'Study_E', 'Study_E', 'Study_F', 'Study_F'],
    'treatment': ['ECT', 'IV_KA', 'ECT', 'IN_EKA', 'IV_KA', 'rTMS',
                  'IN_EKA', 'PO_PSI', 'rTMS', 'PHARM', 'ECT', 'PHARM'],
    'responders': [45, 38, 42, 35, 40, 28, 33, 30, 25, 22, 48, 20],
    'total': [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
    'weeks': [4, 4, 4, 4, 6, 6, 6, 8, 6, 8, 4, 12]  # follow-up time
})

def create_nma_model(data):
    """
    Create Bayesian NMA model using PyMC.

    Model structure:
    - Random effects for studies
    - Treatment effects relative to reference (ECT)
    - Heterogeneity between studies
    - Binomial likelihood for response outcomes
    """

    # Prepare data
    n_studies = len(data)
    n_treatments = len(TREATMENTS)

    # Treatment indices
    treatment_idx = data['treatment'].map(TREATMENTS).values

    # Response data
    r = data['responders'].values
    n = data['total'].values

    with pm.Model() as nma_model:
        # Hyperpriors
        mu = pm.Normal('mu', mu=0, sigma=2)  # Overall mean
        tau = pm.HalfNormal('tau', sigma=0.5)  # Heterogeneity

        # Study-specific random effects
        study_effects = pm.Normal('study_effects', mu=0, sigma=tau, shape=n_studies)

        # Treatment effects (relative to ECT)
        d = pm.Normal('d', mu=0, sigma=1, shape=n_treatments)
        # Fix ECT effect to 0 (reference)
        d_fixed = pm.Deterministic('d_fixed', d - d[0])

        # Linear predictor
        theta = mu + study_effects + d_fixed[treatment_idx]

        # Convert to probability scale
        p = pm.invlogit(theta)

        # Likelihood
        _y = pm.Binomial('y', n=n, p=p, observed=r)

        # Generated quantities for PSA
        # Absolute treatment effects
        _abs_effects = pm.Deterministic('abs_effects', pm.invlogit(mu + d_fixed))

    return nma_model

def fit_nma_model(model, draws=2000, tune=1000, chains=4):
    """Fit the NMA model using MCMC."""
    with model:
        trace = pm.sample(draws=draws, tune=tune, chains=chains, random_seed=42)
    return trace

def generate_posterior_draws(trace, n_draws=1000):
    """
    Generate posterior draws for use in PSA.

    Returns DataFrame with treatment effects and correlations.
    """
    # Extract posterior samples
    posterior = az.extract(trace, num_samples=n_draws)

    # Treatment effects (log odds ratios relative to ECT)
    treatment_effects = {}
    for treatment, idx in TREATMENTS.items():
        if treatment == 'ECT':
            treatment_effects[treatment] = np.zeros(n_draws)  # Reference
        else:
            treatment_effects[treatment] = posterior['d_fixed'].sel(d_fixed_dim_0=idx).values

    # Absolute probabilities
    abs_probs = {}
    for treatment, idx in TREATMENTS.items():
        abs_probs[treatment] = posterior['abs_effects'].sel(abs_effects_dim_0=idx).values

    # Create DataFrame
    draws_df = pd.DataFrame({
        f'{treatment}_logOR': effects
        for treatment, effects in treatment_effects.items()
    })

    # Add absolute probabilities
    for treatment, probs in abs_probs.items():
        draws_df[f'{treatment}_prob'] = probs

    return draws_df

def plot_nma_results(trace, data):
    """Create diagnostic plots for NMA results."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Forest plot of treatment effects
    ax = axes[0, 0]
    treatment_names = list(TREATMENTS.keys())
    means = []
    hdis = []

    for i, treatment in enumerate(treatment_names):
        if treatment == 'ECT':
            means.append(0)
            hdis.append([0, 0])
        else:
            samples = trace.posterior['d_fixed'].sel(d_fixed_dim_0=TREATMENTS[treatment]).values.flatten()
            means.append(np.mean(samples))
            hdis.append(az.hdi(samples, hdi_prob=0.95))

    means = np.array(means)
    hdis = np.array(hdis)

    ax.errorbar(means, range(len(treatment_names)), xerr=[means-hdis[:, 0], hdis[:, 1]-means],
                fmt='o', capsize=3, color='blue', alpha=0.7)
    ax.axvline(0, color='red', linestyle='--', alpha=0.5)
    ax.set_yticks(range(len(treatment_names)))
    ax.set_yticklabels(treatment_names)
    ax.set_xlabel('Log Odds Ratio vs ECT')
    ax.set_title('Treatment Effects (95% HDI)')

    # Posterior distributions
    ax = axes[0, 1]
    for treatment in treatment_names[1:]:  # Skip ECT (reference)
        samples = trace.posterior['d_fixed'].sel(d_fixed_dim_0=TREATMENTS[treatment]).values.flatten()
        sns.kdeplot(samples, label=treatment, ax=ax, alpha=0.7)
    ax.axvline(0, color='red', linestyle='--', alpha=0.5)
    ax.set_xlabel('Log Odds Ratio vs ECT')
    ax.set_title('Posterior Distributions')
    ax.legend()

    # Absolute probabilities
    ax = axes[1, 0]
    abs_means = []
    abs_hdis = []

    for treatment in treatment_names:
        samples = trace.posterior['abs_effects'].sel(abs_effects_dim_0=TREATMENTS[treatment]).values.flatten()
        abs_means.append(np.mean(samples))
        abs_hdis.append(az.hdi(samples, hdi_prob=0.95))

    abs_means = np.array(abs_means)
    abs_hdis = np.array(abs_hdis)

    ax.errorbar(abs_means, range(len(treatment_names)), xerr=[abs_means-abs_hdis[:, 0], abs_hdis[:, 1]-abs_means],
                fmt='o', capsize=3, color='green', alpha=0.7)
    ax.set_yticks(range(len(treatment_names)))
    ax.set_yticklabels(treatment_names)
    ax.set_xlabel('Response Probability')
    ax.set_title('Absolute Response Probabilities')

    # MCMC diagnostics
    ax = axes[1, 1]
    az.plot_energy(trace, ax=ax)
    ax.set_title('Energy Plot (MCMC Diagnostics)')

    plt.tight_layout()
    return fig

def main():
    """Run the complete NMA analysis."""
    print("Setting up Bayesian NMA for TRD treatments...")

    # Create model
    print("Creating NMA model...")
    model = create_nma_model(NMA_DATA)

    # Fit model
    print("Fitting NMA model with MCMC...")
    trace = fit_nma_model(model)

    # Generate posterior draws for PSA
    print("Generating posterior draws for PSA...")
    posterior_draws = generate_posterior_draws(trace)

    # Save results
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)

    # Save posterior draws
    posterior_draws.to_parquet(output_dir / 'nma_posterior_draws.parquet')
    print(f"Saved posterior draws to {output_dir / 'nma_posterior_draws.parquet'}")

    # Save trace for diagnostics
    with open(output_dir / 'nma_trace.pkl', 'wb') as f:
        pickle.dump(trace, f)
    print(f"Saved trace to {output_dir / 'nma_trace.pkl'}")

    # Create diagnostic plots
    print("Creating diagnostic plots...")
    fig = plot_nma_results(trace, NMA_DATA)
    fig.savefig(output_dir / 'nma_diagnostics.png', dpi=300, bbox_inches='tight')
    print(f"Saved diagnostics plot to {output_dir / 'nma_diagnostics.png'}")

    # Print summary
    print("\nNMA Results Summary:")
    print("=" * 50)
    summary = az.summary(trace, var_names=['d_fixed', 'abs_effects'])
    print(summary)

    print("\nNMA analysis complete!")
    print(f"Generated {len(posterior_draws)} posterior draws for PSA")

if __name__ == '__main__':
    main()