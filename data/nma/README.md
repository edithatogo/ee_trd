# Bayesian Network Meta-Analysis for TRD Treatments

This directory contains the Bayesian Network Meta-Analysis (NMA) implementation for comparing treatments for Treatment-Resistant Depression (TRD).

## Overview

The NMA compares the following treatments:

- **ECT**: Electroconvulsive Therapy (reference treatment)
- **IV_KA**: Intravenous Ketamine
- **IN_EKA**: Intranasal Esketamine
- **PO_PSI**: Oral Psilocybin-assisted Therapy
- **rTMS**: Repetitive Transcranial Magnetic Stimulation
- **PHARM**: Pharmacological Augmentation

## Files

- `nma_model.py`: Core Bayesian NMA model implementation using PyMC
- `nma_data.py`: Synthetic NMA dataset based on clinical literature
- `nma_config.yaml`: Configuration file with priors and settings
- `run_nma.py`: Main script to execute the complete NMA analysis
- `nma_posterior_draws.parquet`: Output posterior draws for PSA (generated)
- `nma_diagnostics.png`: Diagnostic plots (generated)
- `nma_trace.pkl`: MCMC trace object for diagnostics (generated)

## Model Structure

### Bayesian Model

- **Random effects**: Study-specific effects to account for heterogeneity
- **Treatment effects**: Relative effects compared to ECT (reference)
- **Heterogeneity**: Between-study variance using half-normal prior
- **Likelihood**: Binomial for response/remission outcomes

### Priors

- Overall mean: Normal(0, 2)
- Heterogeneity: HalfNormal(0, 0.5)
- Treatment effects: Normal(0, 1)

## Usage

### Prerequisites

```bash
pip install pymc>=5.0.0 arviz scipy seaborn
```

### Running the Analysis

```bash
cd data/nma
python run_nma.py
```

This will:

1. Load configuration and data
2. Fit the Bayesian model using MCMC
3. Generate diagnostic plots
4. Export posterior draws for PSA integration

## Outputs

### Posterior Draws (`nma_posterior_draws.parquet`)

Contains 1000 posterior draws with:

- `{treatment}_logOR`: Log odds ratios relative to ECT
- `{treatment}_prob`: Absolute response probabilities

### Integration with Economic Model

The posterior draws are consumed by the economic model to:

- Generate correlated treatment effects in PSA
- Propagate NMA uncertainty through cost-effectiveness analysis
- Enable probabilistic sensitivity analysis with realistic between-study heterogeneity

## Diagnostics

The `nma_diagnostics.png` includes:

- Forest plot of treatment effects with 95% HDIs
- Posterior density plots
- Absolute probability estimates
- MCMC energy diagnostics

## Data Sources

The synthetic data is based on published clinical trials and meta-analyses:

- Kellner et al. (2016): ECT vs Ketamine
- Fond et al. (2014): ECT vs Ketamine
- Daly et al. (2019): Esketamine trials
- Brunoni et al. (2016): rTMS trials
- Davis et al. (2020): Psilocybin trials

## Future Enhancements

- Add time-to-event outcomes using parametric survival models
- Include study-level covariates (dose, duration, etc.)
- Implement mixture-cure models for sustained response
- Add network consistency checks
- Include indirect comparisons validation