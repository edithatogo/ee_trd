#!/usr/bin/env python3
"""
Generate PSA data using NMA posterior draws for treatment effects.

This script creates probabilistic sensitivity analysis (PSA) datasets
by sampling treatment effects from NMA posterior distributions rather
than using fixed Beta distributions.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import sys
from scipy.stats import weibull_min

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

def load_nma_posteriors(nma_path):
    """Load NMA posterior draws."""
    df = pd.read_parquet(nma_path)
    return df

def load_clinical_params(clinical_path):
    """Load clinical parameter distributions for non-NMA parameters."""
    df = pd.read_csv(clinical_path)
    return df

def sample_remission_rates(nma_df, survival_params, n_draws=1000):
    """
    Sample remission rates from NMA posteriors with survival model integration.

    Maps NMA treatment names to model strategy names and computes
    remission probabilities using parametric survival models.
    """
    # Map NMA treatment names to model strategy names
    treatment_mapping = {
        'ECT': 'ECT',
        'IV_KA': 'IV-KA',  # IV Ketamine
        'IN_EKA': 'IN-EKA',
        'PO_PSI': 'PO psilocybin',
        'rTMS': 'rTMS',
        'PHARM': 'Usual care'  # Base pharmacotherapy
    }

    remission_samples = {}

    # Sample indices once for all treatments to ensure correlation
    sampled_indices = np.random.choice(len(nma_df), size=n_draws, replace=True)

    for nma_name, model_name in treatment_mapping.items():
        prob_col = f'{nma_name}_prob'
        if prob_col in nma_df.columns:
            # Use NMA-informed remission rates, but scale them with survival model
            base_rates = nma_df.iloc[sampled_indices][prob_col].values
            
            # Compute time-averaged remission probability over 10-year horizon
            time_points = np.linspace(0, 120, 121)  # Monthly for 10 years
            survival_remission = np.array([compute_remission_probability(model_name, t, survival_params) 
                                         for t in time_points])
            avg_remission = np.mean(survival_remission)
            
            # Scale NMA rates by survival model average
            remission_samples[model_name] = base_rates * (avg_remission / np.mean(base_rates)) if np.mean(base_rates) > 0 else base_rates
        else:
            # Fallback: use survival model directly
            time_points = np.linspace(0, 120, 121)
            survival_remission = np.array([compute_remission_probability(model_name, t, survival_params) 
                                         for t in time_points])
            remission_samples[model_name] = np.full(n_draws, np.mean(survival_remission))

    # Add PO-KA (oral ketamine) - not in NMA, use survival model
    time_points = np.linspace(0, 120, 121)
    survival_remission = np.array([compute_remission_probability('Oral Ketamine', t, survival_params) 
                                 for t in time_points])
    remission_samples['PO-KA'] = np.full(n_draws, np.mean(survival_remission)) + np.random.normal(0, 0.05, n_draws)  # Add some variability

    # Add pharmacotherapy augmentation strategies - use same base with adherence
    base_pharm = remission_samples['Usual care'].copy()
    remission_samples['Usual care + lithium'] = base_pharm * 0.78  # Adherence rate
    remission_samples['Usual care + atypical'] = base_pharm * 0.76  # Adherence rate

    # Add combination treatments
    if 'IV-KA' in remission_samples and 'ECT' in remission_samples:
        remission_samples['KA-ECT'] = np.maximum(remission_samples['ECT'], remission_samples['IV-KA'])  # Combination
        remission_samples['ECT-IV-Ket'] = remission_samples['KA-ECT'].copy()  # Same as KA-ECT
    else:
        remission_samples['KA-ECT'] = remission_samples['ECT'].copy() * 1.1  # Fallback
        remission_samples['ECT-IV-Ket'] = remission_samples['KA-ECT'].copy()

    return remission_samples

def load_survival_params(clinical_df):
    """Extract survival model parameters from clinical inputs."""
    survival_params = {}
    
    # Parse Weibull parameters for each treatment
    treatments = ['ECT', 'Ketamine', 'Esketamine', 'Psilocybin', 'rTMS', 
                  'Usual care + lithium', 'Usual care + atypical', 'Oral Ketamine',
                  'ECT-KA', 'ECT-IV-Ket']
    
    for treatment in treatments:
        # Time-to-response parameters
        shape_response_key = f"{treatment} Weibull shape (time-to-response)"
        scale_response_key = f"{treatment} Weibull scale (time-to-response)"
        
        # Time-to-loss-of-response parameters  
        shape_loss_key = f"{treatment} Weibull shape (time-to-loss-of-response)"
        scale_loss_key = f"{treatment} Weibull scale (time-to-loss-of-response)"
        
        # Extract AU values (could be extended for NZ)
        shape_response = float(clinical_df[clinical_df['Parameter'] == shape_response_key]['AU_Value'].iloc[0]) if not clinical_df[clinical_df['Parameter'] == shape_response_key].empty else 1.5
        scale_response = float(clinical_df[clinical_df['Parameter'] == scale_response_key]['AU_Value'].iloc[0]) if not clinical_df[clinical_df['Parameter'] == scale_response_key].empty else 2.0
        shape_loss = float(clinical_df[clinical_df['Parameter'] == shape_loss_key]['AU_Value'].iloc[0]) if not clinical_df[clinical_df['Parameter'] == shape_loss_key].empty else 1.2
        scale_loss = float(clinical_df[clinical_df['Parameter'] == scale_loss_key]['AU_Value'].iloc[0]) if not clinical_df[clinical_df['Parameter'] == scale_loss_key].empty else 24.0
        
        survival_params[treatment] = {
            'shape_response': shape_response,
            'scale_response': scale_response,
            'shape_loss': shape_loss,
            'scale_loss': scale_loss
        }
    
    return survival_params

def compute_remission_probability(treatment, time_months, survival_params, adherence=1.0):
    """
    Compute remission probability at time t using Weibull survival models.
    
    Uses competing risks: time-to-response vs time-to-treatment-failure.
    """
    if treatment not in survival_params:
        # Fallback for treatments not in survival model
        if 'IV-KA' in treatment or 'Ketamine' in treatment:
            return 0.45 * adherence
        elif 'ECT' in treatment:
            return 0.60 * adherence
        elif 'IN-EKA' in treatment or 'Esketamine' in treatment:
            return 0.36 * adherence
        elif 'PO psilocybin' in treatment or 'Psilocybin' in treatment:
            return 0.40 * adherence
        elif 'rTMS' in treatment:
            return 0.35 * adherence
        elif 'lithium' in treatment or 'atypical' in treatment:
            return 0.25 * adherence
        elif 'PO-KA' in treatment or 'Oral Ketamine' in treatment:
            return 0.42 * adherence
        else:
            return 0.20 * adherence
    
    params = survival_params[treatment]
    
    # Ensure time_months is a numpy array
    time_months = np.asarray(time_months)
    
    # Weibull survival functions
    # Probability of responding by time t
    response_prob = 1 - weibull_min.sf(time_months, params['shape_response'], scale=params['scale_response'])
    
    # Probability of losing response by time t (among responders)
    loss_prob = 1 - weibull_min.sf(time_months, params['shape_loss'], scale=params['scale_loss'])
    
    # Current remission probability = P(responded) * P(not lost response | responded)
    remission_prob = response_prob * (1 - loss_prob)
    
    return remission_prob * adherence

def generate_psa_data(remission_samples, strategies, n_draws=1000):
    """
    Generate PSA dataset with cost and effect for each strategy and draw.
    Generates data for both health_system and societal perspectives.
    """
    psa_rows = []

    # Mock cost and effect calculations (simplified)
    # In a real implementation, this would use the full economic model
    base_cost = 1000
    base_effect = 2.0
    
    # Societal cost components (annual)
    productivity_loss = 2000  # Annual productivity loss for depressed
    informal_care = 10000     # Annual informal care cost

    for draw_idx in range(n_draws):
        for strategy in strategies:
            if strategy in remission_samples:
                remission_rate = remission_samples[strategy][draw_idx]

                # Calculate base costs and effects
                if strategy == 'Usual care':
                    healthcare_cost = base_cost
                    effect = base_effect + (remission_rate - 0.20) * 0.5
                elif 'lithium' in strategy or 'atypical' in strategy:
                    healthcare_cost = base_cost + 200  # Drug cost
                    effect = base_effect + (remission_rate - 0.20) * 0.5
                elif strategy == 'rTMS':
                    healthcare_cost = base_cost + 8000  # rTMS program cost
                    effect = base_effect + (remission_rate - 0.20) * 0.5
                elif strategy == 'PO-KA':
                    healthcare_cost = base_cost + 2000  # Oral ketamine program
                    effect = base_effect + (remission_rate - 0.20) * 0.5
                elif strategy == 'IV-KA':
                    healthcare_cost = base_cost + 5000  # IV ketamine program
                    effect = base_effect + (remission_rate - 0.20) * 0.5
                elif strategy == 'IN-EKA':
                    healthcare_cost = base_cost + 8000  # Esketamine program
                    effect = base_effect + (remission_rate - 0.20) * 0.5
                elif strategy == 'PO psilocybin':
                    healthcare_cost = base_cost + 15000  # Psilocybin program
                    effect = base_effect + (remission_rate - 0.20) * 0.5
                elif strategy == 'ECT':
                    healthcare_cost = base_cost + 8000  # ECT program
                    effect = base_effect + (remission_rate - 0.20) * 0.5
                else:
                    # KA-ECT and other combinations
                    healthcare_cost = base_cost + 10000
                    effect = base_effect + (remission_rate - 0.20) * 0.5

                # Calculate societal costs (healthcare + productivity + informal care)
                depressed_years = (1 - remission_rate) * 10  # Simplified: assume 10-year horizon
                societal_cost = healthcare_cost + depressed_years * (productivity_loss + informal_care)

                # Add health_system perspective
                psa_rows.append({
                    'draw': draw_idx + 1,
                    'strategy': strategy,
                    'cost': healthcare_cost,
                    'effect': effect,
                    'perspective': 'health_system'
                })

                # Add societal perspective
                psa_rows.append({
                    'draw': draw_idx + 1,
                    'strategy': strategy,
                    'cost': societal_cost,
                    'effect': effect,
                    'perspective': 'societal'
                })

    return pd.DataFrame(psa_rows)

def main():
    logger.info("Starting NMA PSA data generation")
    logger.info("Setting up NMA-integrated PSA analysis with survival model integration")

    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "strategies.yml"
    logger.info(f"Loading configuration from: {config_path}")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    strategies = config['strategies']
    logger.info(f"Loaded {len(strategies)} treatment strategies")

    # Load clinical parameters for survival models
    clinical_path = Path(__file__).parent.parent / "data" / "clinical_inputs.csv"
    logger.info(f"Loading clinical parameters from: {clinical_path}")
    clinical_df = load_clinical_params(clinical_path)

    # Extract survival parameters
    logger.info("Extracting survival model parameters from clinical inputs")
    survival_params = load_survival_params(clinical_df)

    # Load NMA posteriors
    nma_path = Path(__file__).parent.parent / "data" / "nma" / "nma_posterior_draws.parquet"
    logger.info(f"Loading NMA posterior draws from: {nma_path}")
    nma_df = load_nma_posteriors(nma_path)

    # Sample remission rates from NMA with survival model integration
    logger.info("Sampling remission rates from NMA posteriors with survival model integration")
    remission_samples = sample_remission_rates(nma_df, survival_params, n_draws=1000)

    # Generate PSA data
    logger.info("Generating PSA dataset with cost and effect calculations")
    psa_df = generate_psa_data(remission_samples, strategies, n_draws=1000)

    # Save PSA data
    output_path = Path(__file__).parent.parent / "data" / "psa_nma_integrated.csv"
    logger.info(f"Saving PSA data to: {output_path}")
    psa_df.to_csv(output_path, index=False)

    # Log summary information
    logger.info(f"Successfully generated PSA data with {len(psa_df)} rows")
    logger.info(f"Saved to {output_path}")
    logger.info(f"Strategies included: {sorted(psa_df['strategy'].unique())}")
    logger.info(f"Draws: {len(psa_df['draw'].unique())}")
    logger.info("NMA PSA data generation completed successfully")

if __name__ == "__main__":
    main()
